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
import colorsys
import importlib.util

# Import Django models
from Website.models import UlosColorThread, UlosCharacteristic

# Install package
def install(package):
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

# Load LLM API key
key_file_path = os.path.join(
    settings.BASE_DIR,
    'static',
    'ColoringFile',
    'deepseek_api.txt'
    )
with open(key_file_path, "r") as key_file:
    api_key = key_file.readline().strip()
print(f"DEBUG: API Key loaded successfully from: {key_file_path}")

# Ulos data (from DB)
dict_ulos_characteristics = {}
dict_ulos_thread_colors1 = {}

# Loads Ulos characteristics and thread colors from the Django database.
def load_ulos_data_from_db():
    global dict_ulos_characteristics, dict_ulos_thread_colors1

    try:
        characteristics = UlosCharacteristic.objects.all()
        for char in characteristics:
            dict_ulos_characteristics[char.NAME] = {
                "garis": char.garis,
                "pola": char.pola,
                "warna_dominasi": char.warna_dominasi,
                "warna_aksen": char.warna_aksen,
                "kontras_warna": char.kontras_warna,
            }

        colors = UlosColorThread.objects.all()
        for color in colors:
            h, s, v = map(int, color.hsv.split(','))
            dict_ulos_thread_colors1[color.CODE] = [h, s, v]
        print("DEBUG: Ulos data loaded from DB successfully.")
    except Exception as e:
        dict_ulos_characteristics = {}
        dict_ulos_thread_colors1 = {}

# DeepSeek generate custom objective function
def create_custom_objective_function(ulos_type, api_key, ulos_colors):
    """ Generates Python code for the objective function based on Ulos characteristics and user-selected colors using the DeepSeek API. """
    char = dict_ulos_characteristics[ulos_type]
    line = char["garis"]
    pattern = char["pola"]
    accent_color = char["warna_aksen"]
    contrast = char["kontras_warna"]

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    list_colors = [dict_ulos_thread_colors1[code] for code in ulos_colors]

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a Senior Programmer"},
            {"role": "user", "content": f"""Buatlah fungsi Python dengan nama calculate_user_color_preferences.
            Fungsi ini merupakan fungsi objektif pada algoritma NSDE (Non-dominated Sorting Differential Evolution) yang mengoptimalkan kombinasi warna pada motif Ulos dengan karakteristik berikut:
            - Garis: {line}
            - Pola: {pattern}
            - Warna aksen: {accent_color}
            - Kontras warna: {contrast}

            Daftar kombinasi Hue, Saturation, Value preferensi pengguna adalah {list_colors}.
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


def create_user_color_threads(api_key, ulos_colors):
    """ Generates recommended color threads based on user-selected colors using the DeepSeek API. """
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    user_selected_colors = {code: dict_ulos_thread_colors1[code] for code in ulos_colors if code in dict_ulos_thread_colors1}

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a Senior Programmer"},
            {"role": "user", "content": f"""
            Saya memiliki daftar warna referensi dalam format HSV (Hue, Saturation, Value): {dict_ulos_thread_colors1}
            Dan warna-warna yang dipilih user: {user_selected_colors}

            Berikan warna lain yang sangat relevan atau mendekati dengan warna {user_selected_colors} dari daftar referensi warna di {dict_ulos_thread_colors1}.
            Output harus berupa dictionary JSON dengan:
            - Key: kode warna asli atau kode warna yang relevan
            - Value: list berisi warna dipilih atau relevan
            - Kembalikan kode warna asli dan relevan

            Pastikan:
            1. Format kode dan value warna dikembalikan dalam daftar seperti pada {dict_ulos_thread_colors1}
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

def get_unique_colors(path_image):
    """ Loads a grayscale and finds its unique pixel values. """
    gray_im = cv2.imread(path_image, cv2.IMREAD_GRAYSCALE)
    
    if gray_im is None:
        print(f"ERROR: Gambar grayscale tidak ditemukan. {path_image}")
        return None, None

    unique_values = np.unique(gray_im).tolist()
    return gray_im, unique_values

def apply_coloring(gray_image, color_dict):
    """Menerapkan pewarnaan pada gambar grayscale berdasarkan dictionary warna."""
    # Membuat array kosong dengan dimensi (tinggi, lebar, 3) untuk menyimpan warna RGB
    color_image = np.zeros((*gray_image.shape, 3), dtype=np.uint8)
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

def save_colored_image(colored_image, ulos_type):
    """
    Saves the colored image to a temporary output directory.
    Returns the relative path to the saved image.
    """
    output_dir = os.path.join(settings.BASE_DIR, 'static', 'ColoringFile', 'output')
    os.makedirs(output_dir, exist_ok=True)
        
    output_filename = f"colored_ulos_{ulos_type}.png"
    output_image_path = os.path.join(output_dir, output_filename)
        
    colored_image_bgr = cv2.cvtColor(colored_image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_image_path, colored_image_bgr)
    print(f"DEBUG: Colored image saved to: {output_image_path}")
        
    relative_output_path = os.path.join('ColoringFile', 'output', output_filename).replace(os.sep, '/')
    return relative_output_path

## Objective Functions

def calculate_michaelson_contrast(hsv_image):
    """Calculates Michaelson contrast from the HSV image."""
    hue_channel = hsv_image[:, :, 0] / 179.0
    min_hue = np.min(hue_channel)
    max_hue = np.max(hue_channel)
    contrast = (max_hue - min_hue) / (max_hue + min_hue)
    return contrast

def calculate_rms_contrast(hsv_image):
    """Calculates RMS contrast from the HSV image."""
    img_bgr = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)
    
    luminance = (0.0722 * img_bgr[..., 0].astype(np.float32) +
                 0.7152 * img_bgr[..., 1].astype(np.float32) +
                 0.2126 * img_bgr[..., 2].astype(np.float32))
    
    mean_luminance = np.mean(luminance)
    rms_contrast = np.sqrt(np.mean((luminance - mean_luminance) ** 2))
    return rms_contrast

def calculate_colorfulness(hsv_image):
    """Calculates the colorfulness of the HSV image."""
    img_rgb = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2RGB)
    
    red, green, blue = cv2.split(img_rgb.astype(np.float32))
    
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


# Coloring Problem

class UlosColoringProblem(Problem):
    """Class defining the Ulos coloring optimization problem for PyMoo."""
    def __init__(self, unique_values, gray_image):
        total_unique_values = len(unique_values)

        # define design variables with bounds
        super().__init__(n_var=total_unique_values,
                         n_obj=5,
                         n_constr=0,
                         xl=np.array([0] * total_unique_values),
                         xu=np.array([len(dict_ulos_thread_colors.values())]
                                     * total_unique_values))
        
        # Simpan parameter yang dibutuhkan untuk evaluasi
        self.unique_values = unique_values
        self.gray_image = gray_image
        self.total_unique_values = total_unique_values

    def _evaluate(self, x, out, *args, **kwargs):
        """Performs evaluation of a population of individuals."""
        indexed_dict = {index: value for index, (key, value)
                        in enumerate(dict_ulos_thread_colors.items())}
        F_values = []
        
        for individual in x:
            list_generated_unique_hsv_values = [indexed_dict[int(i)] for i in individual.flatten()]

            list_original_unique_hsv_values = [tuple([i, i, i]) for i in self.unique_values]

            color_mappings = dict(zip(list_original_unique_hsv_values,
                                      list_generated_unique_hsv_values))
      
            modified_image = np.repeat(self.gray_image[:, :, np.newaxis], 3, axis=2)
            
            for gray_value, color_value in color_mappings.items():
                scalar_gray_value = gray_value[0] 

                color_value_array = np.array(color_value)[np.newaxis, np.newaxis, :]

                modified_image[self.gray_image == scalar_gray_value] = color_value_array

            f1 = calculate_michaelson_contrast(modified_image)
            f2 = calculate_rms_contrast(modified_image)
            f3 = calculate_colorfulness(modified_image)
            f4 = calculate_optimal_unique_colors(modified_image, self.total_unique_values)
            f5 = calculate_user_color_preferences(modified_image)


            F_values.append([-f1, -f2, -f3, -f4, -f5])

        out["F"] = np.array(F_values)

## NSDE Optimization

def run_nsde(problem):
    """Runs the NSDE (Non-dominated Sorting Differential Evolution) algorithm."""
    nsde = NSDE(pop_size=100,
                 variant="DE/rand/1/bin",
                 CR=0.7,
                 F=0.85,
                 de_repair="bounce-back",
                 survival=RankAndCrowding(crowding_func="cd"))
    result = minimize(problem,
                      nsde,
                      ('n_gen', 1),
                      seed=42,
                      verbose=True)
    return result

def get_best_individual(result, unique_values, available_colors):
    """
    Retrieves the 'best' individual from the optimization results based on objective sums.
    """
    pareto_front = result.F
    row_sums = np.sum(pareto_front, axis=1)
    top_index = np.argmin(row_sums)

    best_individual = result.X[top_index].astype(int)
    best_scores = result.F[top_index]

    best_color_dict_converted = {}
    for i, gray_val in enumerate(unique_values):
        color_index = best_individual[i]
        color_index = max(0, min(color_index, len(available_colors) - 1))
        best_color_dict_converted[gray_val] = available_colors[color_index]
        
    return best_individual, best_color_dict_converted, best_scores

def main_coloring_process(ulos_type, ulos_colors, path_image):
    print("\n--- Starting main_coloring_process ---")
    print(f"Input Ulos Type: {ulos_type}")
    print(f"Input Selected Colors: {ulos_colors}")
    print(f"Input Base Image Path: {path_image}")

    load_ulos_data_from_db()

    n_colors = len(ulos_colors)
    
    objective_function_code = create_custom_objective_function(ulos_type, api_key, ulos_colors)
  
    custom_obj_dir = os.path.join(settings.BASE_DIR, 'static', 'ColoringFile')
    os.makedirs(custom_obj_dir, exist_ok=True)
    temp_objective_file_path = os.path.join(custom_obj_dir, "custom_objective_function.py")
    
    with open(temp_objective_file_path, "w") as file:
        file.write(objective_function_code)
  
    spec = importlib.util.spec_from_file_location("custom_obj_func_module", temp_objective_file_path)
    custom_obj_func_module = importlib.util.module_from_spec(spec)
    sys.modules["custom_obj_func_module"] = custom_obj_func_module
    spec.loader.exec_module(custom_obj_func_module)

    calculate_user_color_preferences = custom_obj_func_module.calculate_user_color_preferences
    print("DEBUG: Custom objective function generated and imported successfully.")

    dict_ulos_thread_colors = {}
    recommended_colors_dict = create_user_color_threads(api_key, ulos_colors)
    dict_ulos_thread_colors.update(recommended_colors_dict)
    for code in ulos_colors:
        if code in dict_ulos_thread_colors1:
            dict_ulos_thread_colors[code] = dict_ulos_thread_colors1[code]
        else:
            print(f"WARNING: Color code '{code}' not found in dict_ulos_thread_colors1, skipping.")
    print(f"DEBUG: Recommended Colors Dictionary: {recommended_colors_dict}")

    gray_image, unique_values = get_unique_colors(path_image)
    
    if gray_image is None or unique_values is None:
        print("ERROR: Could not load grayscale image or unique values. Aborting coloring process.")
        return None

    problem = UlosColoringProblem(
        unique_values=unique_values,
        gray_image=gray_image,
        n_colors=n_colors,
        dict_ulos_thread_colors=dict_ulos_thread_colors,
        user_preference_func=calculate_user_color_preferences
        )
    print("DEBUG: UlosColoringProblem defined successfully.")
    print("DEBUG: Running NSDE optimization...")
    result = run_nsde(problem)

    best_individual, best_color_dict, best_scores = get_best_individual(
        result, unique_values, problem.available_colors
    )
        
    print(f"DEBUG: Best individual (color indices): {best_individual}")
    print(f"DEBUG: Best scores (objectives): {best_scores}")
    print(f"DEBUG: Final color mapping: {best_color_dict}")

    
    colored_image = apply_coloring(gray_image, best_color_dict)
    return save_colored_image(colored_image, ulos_type)

if __name__ == '__main__':
    pass