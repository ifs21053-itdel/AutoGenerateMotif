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

def install_if_not_exists(package):
    """Installs a Python package if it's not already present."""
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_if_not_exists("pymoo")
install_if_not_exists("pymoode")
install_if_not_exists("scikit-image")
install_if_not_exists("openai")
install_if_not_exists("Pillow")
install_if_not_exists("opencv-python")

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

def create_custom_objective_function(ulos_type_name, api_key, ulos_selected_color_codes):
    """
    Generates Python code for the objective function based on Ulos characteristics and user-selected colors using the DeepSeek API.
    """
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
    
    Args:
        image_path (str): Path to the grayscale image.
    Returns:
        tuple: (grayscale_image as np.array, list of unique pixel values)
    """
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if image is None:
        print(f"ERROR: Could not load image at {image_path}")
        return None, None

    unique_values = np.unique(image).tolist()
    return image, unique_values

def apply_coloring(grayscale_image_np, best_color_dict_converted):

    if grayscale_image_np.dtype != np.uint8:
        grayscale_image_np = grayscale_image_np.astype(np.uint8)

    colored_image_rgb = np.zeros((grayscale_image_np.shape[0], grayscale_image_np.shape[1], 3), dtype=np.uint8)

    for gray_val, hsv_color in best_color_dict_converted.items():
        h, s, v = hsv_color
        r, g, b = colorsys.hsv_to_rgb(h / 360.0, s / 100.0, v / 100.0)
        
        pixel_rgb = (np.array([r, g, b]) * 255).astype(np.uint8)
        
        colored_image_rgb[grayscale_image_np == gray_val] = pixel_rgb
    return colored_image_rgb

def display_colored_image(colored_image):
    """Displays the colored image using Matplotlib."""
    plt.imshow(colored_image)
    plt.axis('off')
    plt.title("Hasil Pewarnaan Ulos")
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
    hue_channel = hsv_image[:, :, 0] / 179.0
    min_hue = np.min(hue_channel)
    max_hue = np.max(hue_channel)
    if (max_hue + min_hue) == 0:
        return 0.0
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


## Coloring Problem

class UlosColoringProblem(Problem):
    """Class defining the Ulos coloring optimization problem for PyMoo."""
    def __init__(self, unique_grayscale_values, base_image, n_colors, combined_available_colors, user_preference_func):
        
        n_var = len(unique_grayscale_values)
        _xl = 0
        _xu = len(combined_available_colors) - 1

        if _xu < 0:
            raise ValueError("combined_available_colors cannot be empty. No colors to select from.")

        super().__init__(
            n_var=n_var,
            n_obj=5,
            n_constr=0,
            xl=np.full(n_var, _xl, dtype=float),
            xu=np.full(n_var, _xu, dtype=float),
            vtype=int
        )
        
        self.unique_grayscale_values = unique_grayscale_values
        self.base_image = base_image
        self.n_colors = n_colors
        self.combined_available_colors_list = list(combined_available_colors.values())
        self.user_preference_func = user_preference_func

        if self.base_image.dtype != np.uint8:
            print(f"CRITICAL: UlosColoringProblem: base_image dtype is {self.base_image.dtype} at init. Converting to uint8.")
            self.base_image = self.base_image.astype(np.uint8)

    def _evaluate(self, x, out, *args, **kwargs):
        """Performs evaluation of a population of individuals."""
        F_values = []
        
        for individual in x:
            color_dict = {}
            for i, gray_value in enumerate(self.unique_grayscale_values):
                color_index = int(np.round(individual[i]))
                color_index = max(0, min(color_index, len(self.combined_available_colors_list) - 1))
                color_dict[gray_value] = self.combined_available_colors_list[color_index]
            
            hsv_image_raw = np.zeros(self.base_image.shape + (3,), dtype=np.int32)
            for gray_val, hsv_value_raw in color_dict.items():
                hsv_image_raw[self.base_image == gray_val] = np.array(hsv_value_raw, dtype=np.int32)
            
            hsv_image_scaled = hsv_image_raw.astype(np.float32)

            hsv_image_scaled[:, :, 0] = (hsv_image_scaled[:, :, 0] / 360.0) * 179.0
            hsv_image_scaled[:, :, 1] = (hsv_image_scaled[:, :, 1] / 100.0) * 255.0
            hsv_image_scaled[:, :, 2] = (hsv_image_scaled[:, :, 2] / 100.0) * 255.0

            hsv_image_for_cv = np.clip(hsv_image_scaled, 0, 255).astype(np.uint8)

            f1 = calculate_michaelson_contrast(hsv_image_for_cv)
            f2 = calculate_rms_contrast(hsv_image_for_cv)
            f3 = calculate_colorfulness(hsv_image_for_cv)
            f4 = calculate_optimal_unique_colors(hsv_image_for_cv, self.n_colors)
            f5 = self.user_preference_func(hsv_image_for_cv)

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

def get_best_individual(result, unique_values, available_colors_list):
    """
    Retrieves the 'best' individual from the optimization results based on objective sums.
    """
    if result.F is None or len(result.F) == 0:
        print("WARNING: No feasible solutions found by the optimization algorithm.")
        return None, {}, []

    pareto_front = result.F
    row_sums = np.sum(pareto_front, axis=1)
    top_index = np.argmin(row_sums)

    best_individual = result.X[top_index].astype(int)
    best_scores = result.F[top_index]

    best_color_dict_converted = {}
    for i, gray_val in enumerate(unique_values):
        color_index = best_individual[i]
        color_index = max(0, min(color_index, len(available_colors_list) - 1))
        best_color_dict_converted[gray_val] = available_colors_list[color_index]
        
    return best_individual, best_color_dict_converted, best_scores


def main_coloring_process(ulos_type_input, ulos_selected_color_codes_input, base_image_path):

    print("\n--- Starting main_coloring_process ---")
    print(f"Input Ulos Type: {ulos_type_input}")
    print(f"Input Selected Colors: {ulos_selected_color_codes_input}")
    print(f"Input Base Image Path: {base_image_path}")

    load_ulos_data_from_db()

    ulos_type = ulos_type_input
    ulos_colors_codes = ulos_selected_color_codes_input
    n_colors = len(ulos_colors_codes)
    
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
    recommended_colors_dict = user_color_threads(api_key, ulos_colors_codes)
    combined_available_colors.update(recommended_colors_dict)
    for code in ulos_colors_codes:
        if code in DB_ULOS_THREAD_COLORS:
            combined_available_colors[code] = DB_ULOS_THREAD_COLORS[code]
        else:
            print(f"WARNING: Color code '{code}' not found in DB_ULOS_THREAD_COLORS, skipping.")
    print(f"DEBUG: Recommended Colors Dictionary: {recommended_colors_dict}")

    gray_image, unique_values = get_unique_colors(base_image_path)
    
    if gray_image is None or unique_values is None:
        print("ERROR: Could not load grayscale image or unique values. Aborting coloring process.")
        return None, None 

    problem = UlosColoringProblem(
        unique_grayscale_values=unique_values,
        base_image=gray_image,
        n_colors=n_colors,
        combined_available_colors=combined_available_colors,
        user_preference_func=calculate_user_color_preferences_func
        )
    print("DEBUG: UlosColoringProblem defined successfully.")
    print("DEBUG: Running NSDE optimization...")
    result = run_nsde(problem)

    best_individual, best_color_dict, best_scores = get_best_individual(
        result, unique_values, problem.combined_available_colors_list
    )
        
    print(f"DEBUG: Best individual (color indices): {best_individual}")
    print(f"DEBUG: Best scores (objectives): {best_scores}")
    print(f"DEBUG: Final color mapping: {best_color_dict}")

    
    colored_image_rgb = apply_coloring(gray_image, best_color_dict)

    hsv_to_code_map = {tuple(v): k for k, v in DB_ULOS_THREAD_COLORS.items()}
    
    used_color_codes = []
    for hsv_value in best_color_dict.values():
        hsv_tuple = tuple(hsv_value)
        if hsv_tuple in hsv_to_code_map:
            used_color_codes.append(hsv_to_code_map[hsv_tuple])
        else:
            print(f"WARNING: Generated HSV {hsv_value} not found in original DB colors.")

    unique_used_color_codes = sorted(list(set(used_color_codes)))
    print("HSV to Code Map:", hsv_to_code_map)
    print("Used color codes:", used_color_codes)

    relative_output_path = save_colored_image(colored_image_rgb, ulos_type)
    return relative_output_path, unique_used_color_codes

if __name__ == '__main__':
    pass