import subprocess
import sys
import os
import tempfile
import json
import random
import numpy as np
from PIL import Image
import cv2
from pymoo.core.problem import Problem
from pymoode.algorithms import NSDE
from pymoode.survival import RankAndCrowding
from skimage.color import hsv2rgb
from itertools import combinations
from openai import OpenAI
import matplotlib.pyplot as plt
from pymoo.operators.mutation.pm import PolynomialMutation
from pymoo.operators.repair.rounding import RoundingRepair
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
from django.conf import settings
from django.core.cache import cache
import importlib.util
from pymoo.core.callback import Callback

# Import Django models
from Website.models import UlosColorThread, UlosCharacteristic

def install(package):
    """Installs a Python package if it's not already present."""
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install("pymoo")
install("pymoode")
install("scikit-image")
install("openai")
install("Pillow")
install("opencv-python")

# Load API key
key_file_path = os.path.join(
    settings.BASE_DIR,
    'static',
    'ColoringFile',
    'deepseek_api.txt'
    )
with open(key_file_path, "r") as key_file:
    api_key = key_file.readline().strip()

# Ulos data (from DB)
DB_ULOS_CHARACTERISTICS = {}
DB_ULOS_THREAD_COLORS = {}

def load_ulos_data_from_db():
    """Loads Ulos characteristics and thread colors from the Django database."""
    global DB_ULOS_CHARACTERISTICS, DB_ULOS_THREAD_COLORS

    try:
        characteristics = UlosCharacteristic.objects.all()
        for char in characteristics:
            DB_ULOS_CHARACTERISTICS[char.NAME] = {
                "garis": char.garis,
                "pola": char.pola,
                "warna_dominasi": char.warna_dominasi,
                "warna_aksen": char.warna_aksen,
                "kontras_warna": char.kontras_warna,
            }

        colors = UlosColorThread.objects.all()
        for color in colors:
            h, s, v = map(int, color.hsv.split(','))
            DB_ULOS_THREAD_COLORS[color.CODE] = [h, s, v]
        print("DEBUG: Ulos data loaded from DB successfully.")
    except Exception as e:
        DB_ULOS_CHARACTERISTICS = {}
        DB_ULOS_THREAD_COLORS = {}

## DeepSeek API Functions

def create_custom_objective_function(ulos_type_name, api_key, ulos_selected_color_codes):
    """
    Generates Python code for the objective function based on Ulos characteristics and user-selected colors using the DeepSeek API.
    """
    char = DB_ULOS_CHARACTERISTICS[ulos_type_name]
    line = char["garis"]
    pattern = char["pola"]
    accent_color = char["warna_aksen"]
    contrast = char["kontras_warna"]

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    list_colors_hsv = [DB_ULOS_THREAD_COLORS[code] for code in ulos_selected_color_codes]

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a Senior Programmer"},
            {"role": "user", "content": f"""Buatlah fungsi Python dengan nama calculate_user_color_preferences.
            Fungsi ini merupakan fungsi objektif pada algoritma NSDE (Non-dominated Sorting Differential Evolution) yang mengoptimalkan kombinasi warna pada motif Ulos dengan karakteristik berikut:
            - Garis: {line}
            - Pola: {pattern}
            - Warna accent: {accent_color}
            - Kontras warna: {contrast}

            Daftar kombinasi Hue, Saturation, Value preferensi pengguna adalah {list_colors_hsv}.
            Fungsi ini menerima masukan berupa matriks citra dalam HSV color space (dengan Hue 0-179, Saturation 0-255, Value 0-255, dan dtype np.uint8).
            Dari citra tersebut, ekstrak semua kombinasi unik Hue, Saturation, Value.
            Jika daftar kombinasi Hue, Saturation, Value tersebut sama dengan kombinasi Hue, Saturation, Value preferensi pengguna, maka nilai fitness adalah satu (1). Nilai fitness akan berkurang sesuai dengan sejauh mana kesesuaian warna tersebut dengan preferensi yang diberikan, berdasarkan kriteria yang ditentukan.
            Pastikan nilai Hue pada rentang 0-360, konversi ke int32 secara eksplisit, dan pastikan hue_img adalah int sebelum modulo.
            Hasilkan hanya kode program tanpa keterangan tambahan.
            """
            },
        ],
    )
    response_content = response.choices[0].message.content
    return response_content[response_content.find('\n')+1:response_content.rfind('\n')]


def user_color_threads(api_key, ulos_selected_color_codes):
    """
    Generates recommended color threads based on user-selected colors using the DeepSeek API.
    """
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    user_selected_hsv = {code: DB_ULOS_THREAD_COLORS[code] for code in ulos_selected_color_codes if code in DB_ULOS_THREAD_COLORS}

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a Senior Programmer"},
            {"role": "user", "content": f"""
            Saya memiliki daftar warna referensi dalam format HSV (Hue, Saturation, Value): {DB_ULOS_THREAD_COLORS}
            Dan warna-warna yang dipilih user: {user_selected_hsv}

            Berikan warna lain yang sangat relevan atau mendekati dengan warna {user_selected_hsv} dari daftar referensi warna di {DB_ULOS_THREAD_COLORS}.
            Output harus berupa dictionary JSON dengan:
            - Key: kode warna asli atau kode warna yang relevan
            - Value: list berisi warna dipilih atau relevan
            - Kembalikan kode warna asli dan relevan

            Pastikan:
            1. Format kode dan value warna dikembalikan dalam daftar seperti pada {DB_ULOS_THREAD_COLORS}
            2. Satu kode hanya mengandung satu value, untuk warna similiar menggunaakan kode warna asli sebagai key.
            3. Output harus valid JSON

            berikan daftar warna saja, jangan tambahkan keterangan.
            """
            },
        ],
    )
    response_content = response.choices[0].message.content
    return json.loads(response_content[response_content.find('{') : response_content.rfind('}') + 1])


## Utils

def get_unique_colors(image_path):
    """
    Loads a grayscale image and finds its unique pixel values.
    """
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if image is None:
        return None, None

    unique_values = np.unique(image).tolist()
    return image, unique_values

def apply_coloring(gray_image, color_dict):

    color_image = np.zeros((gray_image.shape[0], gray_image.shape[1], 3), dtype=np.uint8)

    for gray_value, hsv in color_dict.items():
        # Normalisasi nilai HSV agar sesuai dengan rentang yang digunakan dalam konversi warna
        hsv_normalized = np.array([[hsv[0] / 360.0,
                                     hsv[1] / 100.0,
                                     hsv[2] / 100.0]], dtype=np.float32)
        # Mengonversi nilai HSV yang telah dinormalisasi ke format RGB
        rgb_color = hsv2rgb(hsv_normalized.reshape(1, 1, 3)).reshape(3) * 255
        color_image[gray_image == int(gray_value)] = rgb_color.astype(np.uint8)
    return color_image

def display_colored_image(colored_image):
    """Displays the colored image using Matplotlib."""
    plt.imshow(colored_image)
    plt.axis('off')
    plt.show()

def save_colored_image(color_image, ulos_type):
    output_dir = os.path.join(settings.BASE_DIR, 'static', 'ColoringFile', 'output')
    os.makedirs(output_dir, exist_ok=True)
        
    output_filename = f"colored_ulos_{ulos_type}.png"
    output_image_path = os.path.join(output_dir, output_filename)
        
    colored_image_bgr = cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_image_path, colored_image_bgr)
        
    relative_output_path = os.path.join('ColoringFile', 'output', output_filename).replace(os.sep, '/')
    return relative_output_path

## Objective Functions

def calculate_michaelson_contrast(hsv_image):
    """Calculates Michaelson contrast from the HSV image."""
    # Ambil channel Hue dan normalisasi ke [0, 1]
    hue_channel = hsv_image[:, :, 0] / 179.0

    # Hitung nilai minimum dan maksimum
    min_hue = np.min(hue_channel)
    max_hue = np.max(hue_channel)

    # Hitung kontras Michelson berdasarkan rumus
    contrast = (max_hue - min_hue) / (max_hue + min_hue)
    return contrast

def calculate_rms_contrast(hsv_image):
    # Mengonversi gambar dari HSV ke BGR dalam
    img_bgr = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)

    # Menghitung luminance berdasarkan rumus standar:
    # Luminance dihitung sebagai kombinasi dari nilai Blue, Green, dan Red dengan bobot yang berbeda
    luminance = (0.0722 * img_bgr[..., 0] +   # Bobot untuk Blue (B)
                 0.7152 * img_bgr[..., 1] +   # Bobot untuk Green (G)
                 0.2126 * img_bgr[..., 2])    # Bobot untuk Red (R)

    # Menghitung rata-rata luminansi dalam gambar
    mean_luminance = np.mean(luminance)

    # Menghitung kontras RMS dengan menggunakan deviasi standar dari nilai luminansi
    rms_contrast = np.sqrt(np.mean((luminance - mean_luminance) ** 2))

    # Mengembalikan nilai RMS Contrast
    return rms_contrast

def calculate_colorfulness(hsv_image):
    """Calculates the colorfulness of the HSV image."""
    img_rgb = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2RGB)
    
    red, green, blue = cv2.split(img_rgb)
    
    rg = red - green
    yb = 0.5 * (red + green) - blue
    
    mean_rg = np.mean(rg)
    mean_yb = np.mean(yb)
    
    std_rg = np.std(rg)
    std_yb = np.std(yb)
    
    colorfulness = np.sqrt(std_rg**2 + std_yb**2) + 0.3 * np.sqrt(mean_rg**2 + mean_yb**2)
    return colorfulness

def calculate_optimal_unique_colors(hsv_image, n_colors):
    """
    Calculates the optimality of unique colors in the HSV image compared to a target number.
    """
    unique_hsv_combinations = np.unique(hsv_image.reshape(-1, hsv_image.shape[2]), axis=0)
    actual_unique_colors = len(unique_hsv_combinations)
    if abs(actual_unique_colors - n_colors) <= 1:
        return 1.0
    else:
        difference = abs(actual_unique_colors - n_colors)
        return 1 / (1 + difference)


## Coloring Problem

class UlosColoringProblem(Problem):
    """Class of problems for Ulos coloring optimization."""
    def __init__(self, unique_grayscale_values, base_image, n_colors, dict_ulos_thread_colors, user_preference_func):
        total_unique_values = len(unique_grayscale_values)

        # define design variables with bounds
        super().__init__(n_var=total_unique_values,
                         n_obj=5,
                         n_constr=0,
                         xl=np.array([0] * total_unique_values),
                         xu=np.array([len(dict_ulos_thread_colors.values())]
                                     * total_unique_values))

        # Simpan parameter yang dibutuhkan untuk evaluasi
        self.unique_values = unique_grayscale_values
        self.gray_image = base_image
        self.total_unique_values = total_unique_values
        self.dict_ulos_thread_colors = list(dict_ulos_thread_colors.values()) # Store as a list for easy indexing
        self.calculate_user_color_preferences = user_preference_func


    def _evaluate(self, x, out, *args, **kwargs):
        """Melakukan evaluasi terhadap populasi individu dan menghasilkan nilai fungsi objektif."""

        # Membuat kamus index ke warna HSV berdasarkan self.dict_ulos_thread_colors
        indexed_dict = {index: value for index, value
                        in enumerate(self.dict_ulos_thread_colors)}

        # initialize an empty list to store objective values for each individual
        F_values = []

        # Iterasi tiap individu (solusi kandidat) dalam populasi x
        for individual in x:
            # Mengubah nilai integer pada individu menjadi warna HSV dari indexed_dict
            # map the design variable `x` to generated unique HSV values
            # change here: convert NumPy array 'i' to a hashable type before using it as a key
            list_generated_unique_hsv_values = [indexed_dict[int(i)] for i in individual.flatten()]

            # Setiap nilai grayscale diubah menjadi tuple (i, i, i) untuk menciptakan warna HSV
            # create original HSV values based on grayscale values
            list_original_unique_hsv_values = [tuple([i, i, i]) for i in self.unique_values]

            # Membuat pemetaan warna dari grayscale ke HSV hasil evolusi
            # create a mapping of original grayscale values to generated color values
            color_mappings = dict(zip(list_original_unique_hsv_values,
                                       list_generated_unique_hsv_values))

            # Membuat array gambar berukuran sama seperti gray_image tapi punya 3 channel (H, S, V)
            # create a 3D array by repeating the 2D array along a new axis
            modified_image = np.repeat(self.gray_image[:, :, np.newaxis], 3, axis=2)

            # apply the color mapping to the image
            for gray_value, color_value in color_mappings.items():
                scalar_gray_value = gray_value[0]  # extract the grayscale scalar value (since all elements are the same)

                # Ubah color_value jadi array dengan dimensi (1,1,3)
                # convert color_value (HSV) to a NumPy array and expand its shape
                color_value_array = np.array(color_value)[np.newaxis, np.newaxis, :]

                # Warnai semua piksel yang sama dengan scalar_gray_value
                # modify the image based on the color mapping
                modified_image[self.gray_image == scalar_gray_value] = color_value_array

            # evaluate objective functions
            f1 = calculate_michaelson_contrast(modified_image)
            f2 = calculate_rms_contrast(modified_image)
            f3 = calculate_colorfulness(modified_image)
            f4 = calculate_optimal_unique_colors(modified_image, self.total_unique_values)
            f5 = self.calculate_user_color_preferences(modified_image) # Use the dynamically loaded function

            # Append the objective values for the current individual
            F_values.append([-f1, -f2, -f3, -f4, -f5])

        out["F"] = np.array(F_values)

# Progress Callback Class 


class NSDEProgressReporter(Callback):
    """
    Callback untuk PyMoo yang hanya melaporkan generasi NSDE saat ini.
    Fungsi utama (main_coloring_process) akan menangani kalkulasi progres keseluruhan.
    """
    def __init__(self, update_main_progress_func):
        super().__init__()
        self.update_main_progress_func = update_main_progress_func

    def notify(self, algorithm):
        current_gen = algorithm.n_gen
        self.update_main_progress_func(current_gen)

# End Progress Callback Class 


## NSDE Optimization

# Modifikasi fungsi run_nsde untuk menerima callback
def run_nsde(problem, termination, callback_instance):
    """Runs the NSDE (Non-dominated Sorting Differential Evolution) algorithm."""
    nsde = NSDE(pop_size=100,
                variant="DE/rand/1/bin",
                CR=0.7,
                F=0.85,
                de_repair="bounce-back",
                survival=RankAndCrowding(crowding_func="cd"))
    result = minimize(problem,
                      nsde,
                      termination,
                      seed=42,
                      verbose=True,
                      callback=callback_instance)
    return result

def get_best_individual(result, unique_values, available_colors):

    # Mengambil nilai fitness semua individu
    pareto_front = result.F

    # Menjumlahkan semua nilai fitness
    row_sums = np.sum(pareto_front, axis=1)

    # Mendapatkan indeks dari baris dengan jumlah tertinggi
    top_index = np.argmin(row_sums)

    # Mengambil representasi kromosom dari individu terbaik (tiap elemen merepresentasikan indeks warna)
    best_individual = result.X[top_index].astype(int)

    # Mengambil skor fitness dari individu terbaik
    best_scores = result.F[top_index]

    # Membentuk dictionary warna terbaik:
    # Mapping dari nilai unik dalam gambar
    best_color_dict_converted = {
        int(k): [int(available_colors[v][0]),
                 int(available_colors[v][1]),
                 int(available_colors[v][2])]
        for k, v in zip(unique_values, best_individual)
    }

    # Mengembalikan individu terbaik dan kamus warna hasil optimasi dalam format integer
    return best_individual, best_color_dict_converted, best_scores


def main_coloring_process(ulos_type_input, ulos_selected_color_codes_input, base_image_path, task_id):

    STAGE_START = 1
    STAGE_LOAD_DB = 5
    STAGE_GEN_OBJ_FUNC = 10
    STAGE_IMPORT_OBJ_FUNC = 15
    STAGE_FETCH_COLORS = 20
    STAGE_NSDE_OPTIMIZATION_START = 25
    STAGE_NSDE_OPTIMIZATION_END = 90
    STAGE_PROCESS_RESULTS = 92
    STAGE_APPLY_COLORS = 95
    STAGE_SAVE_IMAGE = 98
    STAGE_COMPLETED = 100

    TOTAL_NSDE_GENERATIONS = 3 
    current_nsde_generation = 0 

    def update_progress(progress):
        """Helper function to update for overall process progress."""
        cache.set(task_id, {'progress': progress}, timeout=3600)

    def update_nsde_progress_in_main(gen):
        nonlocal current_nsde_generation
        current_nsde_generation = gen
        
        # Hitung kontribusi NSDE terhadap progres keseluruhan
        nsde_progress_range = STAGE_NSDE_OPTIMIZATION_END - STAGE_NSDE_OPTIMIZATION_START
        if TOTAL_NSDE_GENERATIONS > 0:
            progress_within_nsde_range = (current_nsde_generation / TOTAL_NSDE_GENERATIONS) * nsde_progress_range
        else:
            progress_within_nsde_range = nsde_progress_range # Jika 0 generasi, lompat ke akhir rentang
            
        total_progress = int(STAGE_NSDE_OPTIMIZATION_START + progress_within_nsde_range)
        
        update_progress(total_progress)

    try:
        update_progress(STAGE_START)
        update_progress(STAGE_LOAD_DB)
        load_ulos_data_from_db()

        ulos_type = ulos_type_input
        ulos_colors_codes = ulos_selected_color_codes_input
        n_colors = len(ulos_colors_codes)
        
        update_progress(STAGE_GEN_OBJ_FUNC)
        objective_function_code = create_custom_objective_function(ulos_type, api_key, ulos_colors_codes)
        
        custom_obj_dir = os.path.join(settings.BASE_DIR, 'static', 'ColoringFile')
        os.makedirs(custom_obj_dir, exist_ok=True)
        temp_objective_file_path = os.path.join(custom_obj_dir, "custom_objective_function.py")
        
        with open(temp_objective_file_path, "w") as file:
            file.write(objective_function_code)
        
        update_progress(STAGE_IMPORT_OBJ_FUNC)
        spec = importlib.util.spec_from_file_location("custom_obj_func_module", temp_objective_file_path)
        custom_obj_func_module = importlib.util.module_from_spec(spec)
        sys.modules["custom_obj_func_module"] = custom_obj_func_module
        spec.loader.exec_module(custom_obj_func_module)

        calculate_user_color_preferences_func = custom_obj_func_module.calculate_user_color_preferences
        print("DEBUG: Custom objective function generated and imported successfully.")
        update_progress(STAGE_FETCH_COLORS)

        dict_ulos_thread_colors = {}
        recommended_colors_dict = user_color_threads(api_key, ulos_colors_codes)
        dict_ulos_thread_colors.update(recommended_colors_dict)

        # Update dengan warna dari DB tanpa if
        dict_ulos_thread_colors.update({
            code: DB_ULOS_THREAD_COLORS[code]
            for code in ulos_colors_codes & DB_ULOS_THREAD_COLORS.keys()
        })
        print(f"DEBUG: Recommended Colors Dictionary: {recommended_colors_dict}")

        gray_image, unique_values = get_unique_colors(base_image_path)
        
        if gray_image is None or unique_values is None:
            update_progress(STAGE_COMPLETED)
            return None, None 

        problem = UlosColoringProblem(
            unique_grayscale_values=unique_values,
            base_image=gray_image,
            n_colors=n_colors,
            dict_ulos_thread_colors=dict_ulos_thread_colors,
            user_preference_func=calculate_user_color_preferences_func
            )
        print("DEBUG: UlosColoringProblem defined successfully.")
        
        termination = get_termination("n_gen", TOTAL_NSDE_GENERATIONS)

        nsde_reporter_callback = NSDEProgressReporter(update_nsde_progress_in_main)

        print("DEBUG: Running NSDE optimization...")
        update_progress(STAGE_NSDE_OPTIMIZATION_START) 
        
        result = run_nsde(problem, termination, nsde_reporter_callback)

        update_progress(STAGE_NSDE_OPTIMIZATION_END)

        update_progress(STAGE_PROCESS_RESULTS)
        best_individual, best_color_dict, best_scores = get_best_individual(
            result, unique_values, list(dict_ulos_thread_colors.values())
        )
            
        print(f"DEBUG: Best individual (color indices): {best_individual}")
        print(f"DEBUG: Best scores (objectives): {best_scores}")
        print(f"DEBUG: Final color mapping: {best_color_dict}")

        update_progress(STAGE_APPLY_COLORS)
        colored_image_rgb = apply_coloring(gray_image, best_color_dict)

        hsv_to_code_map = {tuple(v): k for k, v in DB_ULOS_THREAD_COLORS.items()}
        
        used_color_codes = []
        for hsv_value in best_color_dict.values():
            hsv_tuple = tuple(hsv_value)
            if hsv_tuple in hsv_to_code_map:
                used_color_codes.append(hsv_to_code_map[hsv_tuple])

        unique_used_color_codes = sorted(list(set(used_color_codes)))
        print("HSV to Code Map:", hsv_to_code_map)
        print("Used color codes:", unique_used_color_codes)

        update_progress(STAGE_SAVE_IMAGE)
        relative_output_path = save_colored_image(colored_image_rgb, ulos_type)
        
        # Final success update
        final_result = {
            'progress': STAGE_COMPLETED,
            'status': 'Completed',
            'colored_image_url': relative_output_path,
            'unique_used_color_codes': unique_used_color_codes
        }
        cache.set(task_id, final_result, timeout=3600)
        return relative_output_path, unique_used_color_codes

    except Exception as e:
        cache.set(task_id, {
            'progress': STAGE_COMPLETED
        }, timeout=3600)
        return None, None

if __name__ == '__main__':
    pass