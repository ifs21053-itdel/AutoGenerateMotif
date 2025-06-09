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
from multiprocessing.pool import ThreadPool
from pymoo.core.problem import StarmapParallelization
from pymoo.core.problem import ElementwiseProblem

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
print(f"DEBUG: API Key loaded successfully from: {key_file_path}")

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
        print(f"ERROR: Failed to load Ulos data from DB: {e}")

## DeepSeek API Functions

# Cache for generated objective functions and recommended colors
_objective_function_cache = {}
_recommended_colors_cache = {}

def create_custom_objective_function(ulos_type_name, api_key, ulos_selected_color_codes):
    """
    Generates Python code for the objective function based on Ulos characteristics
    and user-selected colors using the DeepSeek API.
    """
    cache_key = (ulos_type_name, tuple(sorted(ulos_selected_color_codes)))
    if cache_key in _objective_function_cache:
        print("DEBUG: Using cached custom objective function.")
        return _objective_function_cache[cache_key]

    if ulos_type_name not in DB_ULOS_CHARACTERISTICS:
        raise ValueError(f"Ulos type '{ulos_type_name}' not found in database characteristics.")
    
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
    cleaned_content = response_content[response_content.find('\n')+1:response_content.rfind('\n')]
    _objective_function_cache[cache_key] = cleaned_content
    return cleaned_content


def create_user_color_threads(api_key, ulos_selected_color_codes):
    """
    Generates recommended color threads based on user-selected colors using the DeepSeek API.
    """
    cache_key = tuple(sorted(ulos_selected_color_codes))
    if cache_key in _recommended_colors_cache:
        print("DEBUG: Using cached recommended colors.")
        return _recommended_colors_cache[cache_key]

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
    parsed_content = json.loads(response_content[response_content.find('{') : response_content.rfind('}') + 1])
    _recommended_colors_cache[cache_key] = parsed_content
    return parsed_content

## Utils

def get_unique_colors(image_path):
    """
    Loads a grayscale image and finds its unique pixel values.
    """
    gray_im = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if gray_im is None:
        print(f"ERROR: Could not load image at {image_path}")
        return None, None

    unique_values = np.unique(gray_im).tolist()
    return gray_im, unique_values

def apply_coloring(gray_image, best_color_dict_converted):

    if gray_image.dtype != np.uint8:
        gray_image = gray_image.astype(np.uint8)

    colored_image_rgb = np.zeros((gray_image.shape[0], gray_image.shape[1], 3), dtype=np.uint8)

    for gray_val, hsv_color in best_color_dict_converted.items():
        h, s, v = hsv_color
        # Ensure HSV values are in the correct range for colorsys
        # H: 0-360, S: 0-1, V: 0-1
        r, g, b = colorsys.hsv_to_rgb(h / 360.0, s / 100.0, v / 100.0)
        
        pixel_rgb = (np.array([r, g, b]) * 255).astype(np.uint8)
        
        colored_image_rgb[gray_image == gray_val] = pixel_rgb
    return colored_image_rgb

def display_colored_image(colored_image):
    """Displays the colored image using Matplotlib."""
    plt.imshow(colored_image)
    plt.axis('off')
    plt.show()

def save_colored_image(colored_image_rgb, ulos_type):
    """
    Saves the colored image to a temporary output directory.
    Returns the relative path to the saved image.
    """
    output_dir = os.path.join(settings.BASE_DIR, 'static', 'ColoringFile', 'output')
    os.makedirs(output_dir, exist_ok=True)
        
    output_filename = f"colored_ulos_{ulos_type}.png"
    output_image_path = os.path.join(output_dir, output_filename)
        
    colored_image_bgr = cv2.cvtColor(colored_image_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_image_path, colored_image_bgr)
    print(f"DEBUG: Colored image saved to: {output_image_path}")
        
    relative_output_path = os.path.join('ColoringFile', 'output', output_filename).replace(os.sep, '/')
    return relative_output_path

## Objective Functions

def calculate_michaelson_contrast(hsv_image):
    """Calculates Michaelson contrast from the HSV image."""
    # Ensure the hue channel is correctly scaled for contrast calculation if it's 0-179 from OpenCV
    # If the hsv_image comes from modified_image, hue is 0-360
    # Let's assume the generated objective function also scales hue appropriately.
    # For now, sticking to the existing scaling if the image is directly from OpenCV read as HSV
    # If the image is generated by our coloring, its H will be 0-360, so divide by 360.0
    hue_channel = hsv_image[:, :, 0] / 360.0 # Assuming HSV from our coloring where H is 0-360
    min_hue = np.min(hue_channel)
    max_hue = np.max(hue_channel)
    # Avoid division by zero if max_hue + min_hue is zero (e.g., uniform hue image)
    contrast = (max_hue - min_hue) / (max_hue + min_hue + 1e-6) # Add small epsilon
    return contrast

def calculate_rms_contrast(hsv_image):
    """Calculates RMS contrast from the HSV image."""
    # Ensure conversion from HSV to BGR is correct.
    # If the hsv_image has H 0-360, S 0-100, V 0-100, cv2.cvtColor will expect H 0-179, S 0-255, V 0-255.
    # So, we need to convert to an OpenCV-compatible HSV first, then to BGR.
    hsv_for_cv = hsv_image.copy()
    hsv_for_cv[:,:,0] = hsv_for_cv[:,:,0] / 2 # Scale Hue from 0-360 to 0-179
    hsv_for_cv[:,:,1] = hsv_for_cv[:,:,1] * 2.55 # Scale Saturation from 0-100 to 0-255
    hsv_for_cv[:,:,2] = hsv_for_cv[:,:,2] * 2.55 # Scale Value from 0-100 to 0-255
    hsv_for_cv = hsv_for_cv.astype(np.uint8) # Ensure it's uint8

    img_bgr = cv2.cvtColor(hsv_for_cv, cv2.COLOR_HSV2BGR)
    
    luminance = (0.0722 * img_bgr[..., 0] +   # Bobot untuk Blue (B)
                  0.7152 * img_bgr[..., 1] +   # Bobot untuk Green (G)
                  0.2126 * img_bgr[..., 2])    # Bobot untuk Red (R)
    
    mean_luminance = np.mean(luminance)
    rms_contrast = np.sqrt(np.mean((luminance - mean_luminance) ** 2))
    return rms_contrast

def calculate_colorfulness(hsv_image):
    """Calculates the colorfulness of the HSV image."""
    # Similar scaling concern as RMS contrast for cv2.cvtColor
    hsv_for_cv = hsv_image.copy()
    hsv_for_cv[:,:,0] = hsv_for_cv[:,:,0] / 2 # Scale Hue from 0-360 to 0-179
    hsv_for_cv[:,:,1] = hsv_for_cv[:,:,1] * 2.55 # Scale Saturation from 0-100 to 0-255
    hsv_for_cv[:,:,2] = hsv_for_cv[:,:,2] * 2.55 # Scale Value from 0-100 to 0-255
    hsv_for_cv = hsv_for_cv.astype(np.uint8) # Ensure it's uint8

    img_rgb = cv2.cvtColor(hsv_for_cv, cv2.COLOR_HSV2RGB)
    
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

class UlosColoringProblem(ElementwiseProblem): # Changed base class
    """Class defining the Ulos coloring optimization problem for PyMoo."""
    def __init__(self, unique_grayscale_values, base_image, n_colors, combined_available_colors, user_preference_func, **kwargs):
        total_unique_values = len(unique_grayscale_values)
        
        # Store combined_available_colors as an attribute
        self.combined_available_colors = combined_available_colors
        # Create a list of the VALUES from the dictionary for easy indexing
        self.combined_available_colors_list = list(combined_available_colors.values())

        # define design variables with bounds
        super().__init__(n_var=total_unique_values,
                         n_obj=5,
                         n_constr=0,
                         xl=np.array([0] * total_unique_values),
                         # The upper bound should be the last valid index of the list of available colors
                         xu=np.array([len(self.combined_available_colors_list) - 1] 
                                     * total_unique_values),
                         **kwargs) # Pass kwargs to the super constructor for the runner

        # Simpan parameter yang dibutuhkan untuk evaluasi
        self.unique_values = unique_grayscale_values
        self.gray_image = base_image
        self.total_unique_values = total_unique_values
        self.calculate_user_color_preferences = user_preference_func # Store the passed function

    def _evaluate(self, x, out, *args, **kwargs): # x now represents a single individual
        """Melakukan evaluasi terhadap satu individu dan menghasilkan nilai fungsi objektif."""

        # Membuat kamus index ke warna HSV berdasarkan self.combined_available_colors_list
        indexed_dict = {index: value for index, value 
                                 in enumerate(self.combined_available_colors_list)}

        # Mengubah nilai integer pada individu menjadi warna HSV dari indexed_dict
        # x.flatten() is used because x is an array, even for a single individual
        list_generated_unique_hsv_values = [indexed_dict[int(i)] for i in x.flatten()]

        # Setiap nilai grayscale diubah menjadi tuple (i, i, i) untuk menciptakan warna HSV
        # This assumes unique_values are actual grayscale pixel values, e.g., 0-255
        # The tuple (i, i, i) represents the "key" from the grayscale image.
        list_original_unique_grayscale_values = [i for i in self.unique_values]

        # Membuat pemetaan warna dari grayscale ke HSV hasil evolusi
        color_mappings = dict(zip(list_original_unique_grayscale_values,
                                  list_generated_unique_hsv_values))

        # Membuat array gambar berukuran sama seperti gray_image tapi punya 3 channel (H, S, V)
        # Initialize with a default color if a grayscale value is not mapped
        modified_image = np.zeros((self.gray_image.shape[0], self.gray_image.shape[1], 3), dtype=np.int32) 
        # Changed to int32 to prevent overflow during intermediate calculations or if H is 0-360 etc.

        # apply the color mapping to the image
        for gray_value, color_value in color_mappings.items():
            # Warnai semua piksel yang sama dengan gray_value
            # Ensure color_value is applied correctly to the image where gray_image matches gray_value
            modified_image[self.gray_image == gray_value] = color_value


        # Convert modified_image to uint8 HSV (0-179, 0-255, 0-255) for user_color_preferences if needed,
        # or ensure calculate_user_color_preferences can handle H 0-360.
        # The prompt for DeepSeek says "(dengan Hue 0-179, Saturation 0-255, Value 0-255, dan dtype np.uint8)".
        # Our `color_value` from DB_ULOS_THREAD_COLORS is [H, S, V] where H is 0-360, S 0-100, V 0-100.
        # We need to ensure `modified_image` is in the format expected by `calculate_user_color_preferences`.

        # Let's assume the generated objective function expects 0-179 for Hue, 0-255 for S and V.
        # So we scale the modified_image (which is H 0-360, S 0-100, V 0-100)
        hsv_image_for_objectives = modified_image.astype(np.float32).copy()
        hsv_image_for_objectives[:,:,0] = hsv_image_for_objectives[:,:,0] / 2 # Hue 0-360 to 0-179
        hsv_image_for_objectives[:,:,1] = hsv_image_for_objectives[:,:,1] * 2.55 # Saturation 0-100 to 0-255
        hsv_image_for_objectives[:,:,2] = hsv_image_for_objectives[:,:,2] * 2.55 # Value 0-100 to 0-255
        hsv_image_for_objectives = hsv_image_for_objectives.astype(np.uint8) # Cast to uint8

        # evaluate objective functions
        f1 = calculate_michaelson_contrast(hsv_image_for_objectives)
        f2 = calculate_rms_contrast(hsv_image_for_objectives)
        f3 = calculate_colorfulness(hsv_image_for_objectives)
        f4 = calculate_optimal_unique_colors(hsv_image_for_objectives, self.total_unique_values)
        f5 = self.calculate_user_color_preferences(hsv_image_for_objectives) 

        # Assign the objective values to out["F"] for the single individual
        out["F"] = np.array([-f1, -f2, -f3, -f4, -f5]) 

## NSDE Optimization

def run_nsde(problem):
    """Runs the NSDE (Non-dominated Sorting Differential Evolution) algorithm."""
    nsde = NSDE(pop_size=100, # Consider reducing this if unique_values is very high
                variant="DE/rand/1/bin",
                CR=0.7,
                F=0.85,
                de_repair="bounce-back",
                survival=RankAndCrowding(crowding_func="cd"))
    result = minimize(problem,
                      nsde,
                      # Use a proper termination criteria instead of just 1 generation
                      # A low number of generations if quality is not critical, or 'n_evals'
                      # ('n_gen', 5) could be a start. Or ('n_evals', 10000)
                      ('n_gen', 1), # Increased generations slightly for potentially better results
                      seed=42,
                      verbose=True)
    return result

def get_best_individual(result, unique_values, available_colors_list):
    """
    Retrieves the 'best' individual from the optimization results based on objective sums.
    """
    # Mengambil nilai fitness semua individu
    pareto_front = result.F

    # Menjumlahkan semua nilai fitness
    # For minimization, we want the smallest sum. If objectives are negative (maximize),
    # then argmin of negative sum is max of positive sum.
    row_sums = np.sum(pareto_front, axis=1)

    # Mendapatkan indeks dari baris dengan jumlah tertinggi (since objectives are negated for maximization)
    # If objectives are negated (f1 to f5 are maximized), then argmin of negative sum is argmax of positive sum.
    # So `np.argmin(row_sums)` is correct for maximizing the sum of objectives (which are negated).
    top_index = np.argmin(row_sums) 

    # Mengambil representasi kromosom dari individu terbaik (tiap elemen merepresentasikan indeks warna)
    best_individual = result.X[top_index].astype(int)

    # Mengambil skor fitness dari individu terbaik
    best_scores = result.F[top_index]

    # Membentuk dictionary warna terbaik:
    # Mapping dari nilai unik dalam gambar (grayscale values) ke warna HSV hasil optimasi
    best_color_dict_converted = {
        int(k): [int(available_colors_list[v][0]),
                 int(available_colors_list[v][1]),
                 int(available_colors_list[v][2])]
        for k, v in zip(unique_values, best_individual)
    }

    # Mengembalikan individu terbaik dan kamus warna hasil optimasi dalam format integer
    return best_individual, best_color_dict_converted, best_scores


def main_coloring_process(ulos_type_input, ulos_selected_color_codes_input, base_image_path):

    print("\n--- Starting main_coloring_process ---")
    print(f"Input Ulos Type: {ulos_type_input}")
    print(f"Input Selected Colors: {ulos_selected_color_codes_input}")
    print(f"Input Base Image Path: {base_image_path}")

    # Load Ulos data from DB only once
    load_ulos_data_from_db()

    ulos_type = ulos_type_input
    ulos_colors_codes = ulos_selected_color_codes_input
    n_colors = len(ulos_colors_codes)
    
    # --- DeepSeek API calls (now cached) ---
    objective_function_code = create_custom_objective_function(ulos_type, api_key, ulos_colors_codes)
    
    custom_obj_dir = os.path.join(settings.BASE_DIR, 'static', 'ColoringFile')
    os.makedirs(custom_obj_dir, exist_ok=True)
    temp_objective_file_path = os.path.join(custom_obj_dir, "custom_objective_function.py")
    
    with open(temp_objective_file_path, "w") as file:
        file.write(objective_function_code)
    
    spec = importlib.util.spec_from_file_location("custom_obj_func_module", temp_objective_file_path)
    custom_obj_func_module = importlib.util.module_from_spec(spec)
    sys.modules["custom_obj_func_module"] = custom_obj_func_module
    spec.loader.exec_module(custom_obj_func_module)

    calculate_user_color_preferences_func = custom_obj_func_module.calculate_user_color_preferences
    print("DEBUG: Custom objective function generated and imported successfully.")

    combined_available_colors = {}
    # Use cached recommended colors
    recommended_colors_dict = create_user_color_threads(api_key, ulos_colors_codes)
    combined_available_colors.update(recommended_colors_dict)
    for code in ulos_colors_codes:
        if code in DB_ULOS_THREAD_COLORS:
            combined_available_colors[code] = DB_ULOS_THREAD_COLORS[code]
        else:
            print(f"WARNING: Color code '{code}' not found in DB_ULOS_THREAD_COLORS, skipping.")
    print(f"DEBUG: Recommended Colors Dictionary: {recommended_colors_dict}")
    # --- End DeepSeek API calls ---

    gray_image, unique_values = get_unique_colors(base_image_path)
    
    if gray_image is None or unique_values is None:
        print("ERROR: Could not load grayscale image or unique values. Aborting coloring process.")
        return None, None 
    
    # --- Parallelization setup ---
    n_threads = 8  # You can adjust this based on your CPU cores
    pool = ThreadPool(n_threads)
    runner = StarmapParallelization(pool.starmap)
    print(f"DEBUG: Initialized ThreadPool with {n_threads} threads for parallelization.")
    # ---------------------------

    problem = UlosColoringProblem(
        unique_grayscale_values=unique_values,
        base_image=gray_image,
        n_colors=n_colors,
        combined_available_colors=combined_available_colors,
        user_preference_func=calculate_user_color_preferences_func,
        # THIS IS THE KEY CHANGE: Pass the runner explicitly
        elementwise_runner=runner 
    )
    print("DEBUG: UlosColoringProblem defined successfully with parallelization runner.")
    print("DEBUG: Running NSDE optimization...")
    
    # Running optimization
    result = run_nsde(problem)

    best_individual, best_color_dict, best_scores = get_best_individual(
        result, unique_values, problem.combined_available_colors_list
    )
        
    print(f"DEBUG: Best individual (color indices): {best_individual}")
    print(f"DEBUG: Best scores (objectives): {best_scores}")
    print(f"DEBUG: Final color mapping: {best_color_dict}")

    # Ensure the colored image generated for display uses the correct HSV ranges (H 0-360, S 0-100, V 0-100)
    # The `apply_coloring` function already handles conversion to RGB from these ranges.
    colored_image_rgb = apply_coloring(gray_image, best_color_dict)

    hsv_to_code_map = {tuple(v): k for k, v in DB_ULOS_THREAD_COLORS.items()}
    
    used_color_codes = []
    for hsv_value in best_color_dict.values():
        hsv_tuple = tuple(hsv_value)
        if hsv_tuple in hsv_to_code_map:
            used_color_codes.append(hsv_to_code_map[hsv_tuple])
        else:
            print(f"WARNING: Generated HSV {hsv_value} not found in original DB colors. This might mean DeepSeek suggested a slightly different shade or a new color.")

    unique_used_color_codes = sorted(list(set(used_color_codes)))
    print("HSV to Code Map:", hsv_to_code_map)
    print("Used color codes:", unique_used_color_codes) # Print unique codes for clarity

    # --- Close the pool after optimization ---
    pool.close()
    pool.join() # Wait for all threads to finish
    print("DEBUG: ThreadPool closed.")
    # -----------------------------------------

    relative_output_path = save_colored_image(colored_image_rgb, ulos_type)
    return relative_output_path, unique_used_color_codes

if __name__ == '__main__':
    # This block is for testing purposes if you run the script directly.
    # It won't be hit when Django calls main_coloring_process.
    # You would need to mock Django settings and database for a full test.
    print("This script is intended to be called from a Django view.")
    print("Please ensure your Django environment is set up to test this.")