import subprocess
import sys
import os
import json
import numpy as np
import cv2
from pymoo.core.problem import Problem
from pymoode.algorithms import NSDE
from pymoode.survival import RankAndCrowding
from skimage.color import hsv2rgb
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
from typing import List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum
import math

# Import Django models
from Website.models import UlosColorThread, UlosCharacteristic

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

# ========== UPDATED COLOR SCHEME ANALYZER ==========

class ColorSchemeType(Enum):
    MONOCHROMATIC = "Monochromatic"
    ANALOGOUS = "Analogous"
    COMPLEMENTARY = "Complementary"
    TRIADIC = "Triadic"           
    TETRADIC = "Tetradic"         
    ACHROMATIC = "Achromatic"

@dataclass
class Color:
    code: str
    hue: float
    saturation: float
    value: float
    
    def __post_init__(self):
        # Normalize hue to 0-360 range
        self.hue = self.hue % 360
    
    def is_achromatic(self) -> bool:
        """Check if color is achromatic (low saturation)"""
        return self.saturation <= 20
    
    def hue_distance(self, other: 'Color') -> float:
        """Calculate shortest distance between two hues on color wheel"""
        diff = abs(self.hue - other.hue)
        return min(diff, 360 - diff)

class UlosColorSchemeAnalyzer:
    """
    Updated Color Scheme Analyzer dengan Tetradic dan Triadic
    """
    def __init__(self):
        self.colors = {}
        self._load_colors_from_db()
    
    def _load_colors_from_db(self):
        """Load colors from existing DB_ULOS_THREAD_COLORS"""
        for code, hsv_values in DB_ULOS_THREAD_COLORS.items():
            h, s, v = hsv_values
            self.colors[code] = Color(code, h, s, v)
    
    def refresh_colors(self):
        """Refresh colors when DB data is updated"""
        self._load_colors_from_db()
    
    def find_similar_colors(self, primary_color_code: str, count: int = 3) -> List[str]:
        """Find similar colors based on hue, saturation, and value proximity"""
        if primary_color_code not in self.colors:
            return []
        
        primary = self.colors[primary_color_code]
        similarities = []
        
        for code, color in self.colors.items():
            if code == primary_color_code:
                continue
            
            # Calculate similarity score
            hue_diff = primary.hue_distance(color)
            sat_diff = abs(primary.saturation - color.saturation)
            val_diff = abs(primary.value - color.value)
            
            # Weighted similarity (hue is most important)
            similarity = (
                (360 - hue_diff) * 0.5 +
                (100 - sat_diff) * 0.3 +
                (100 - val_diff) * 0.2
            )
            
            similarities.append((code, similarity))
        
        # Sort by similarity and return top matches
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [code for code, _ in similarities[:count]]
    
    def _is_triadic(self, chromatic_colors: List[Color]) -> bool:
        """Check if colors form a triadic scheme (3 colors ~120° apart)"""
        if len(chromatic_colors) != 3:
            return False
        
        hues = sorted([c.hue for c in chromatic_colors])
        
        # Calculate distances between adjacent hues
        dist1 = abs(hues[1] - hues[0])
        dist2 = abs(hues[2] - hues[1])
        dist3 = abs((hues[0] + 360) - hues[2])  # wrap around
        
        # Check if distances are approximately 120° (±30°)
        target = 120
        tolerance = 30
        
        distances = [dist1, dist2, dist3]
        valid_distances = sum(1 for d in distances if abs(d - target) <= tolerance)
        
        return valid_distances >= 2
    
    def _is_tetradic(self, chromatic_colors: List[Color]) -> bool:
        """Check if colors form a tetradic scheme (4 colors, 2 complementary pairs)"""
        if len(chromatic_colors) != 4:
            return False
        
        hues = [c.hue for c in chromatic_colors]
        complementary_pairs = 0
        
        # Check all combinations for complementary pairs (180° ± 30°)
        for i in range(len(hues)):
            for j in range(i + 1, len(hues)):
                distance = min(abs(hues[i] - hues[j]), 360 - abs(hues[i] - hues[j]))
                if abs(distance - 180) <= 30:  # Complementary tolerance
                    complementary_pairs += 1
        
        # Tetradic should have at least 1 complementary pair
        return complementary_pairs >= 1
    
    def analyze_color_scheme(self, color_codes: List[str]) -> Dict:
        if not color_codes:
            return {"scheme_type": ColorSchemeType.ACHROMATIC, "description": "No colors provided"}
        
        colors = [self.colors[code] for code in color_codes if code in self.colors]
        
        if not colors:
            return {"scheme_type": ColorSchemeType.ACHROMATIC, "description": "Invalid color codes"}
        
        # Count achromatic colors
        achromatic_colors = [c for c in colors if c.is_achromatic()]
        chromatic_colors = [c for c in colors if not c.is_achromatic()]
        
        # If all colors are achromatic
        if len(chromatic_colors) == 0:
            return {
                "scheme_type": ColorSchemeType.ACHROMATIC,
                "description": "All colors are neutral (black, white, gray)",
                "colors": color_codes,
                "achromatic_count": len(achromatic_colors),
                "chromatic_count": 0,
                "hue_range": 0,
                "color_harmony_score": 0.8  # Neutral harmony
            }
        
        # Analyze chromatic colors only for pattern detection
        if len(chromatic_colors) == 1:
            return {
                "scheme_type": ColorSchemeType.MONOCHROMATIC,
                "description": "Single color with neutral variations",
                "colors": color_codes,
                "hue_range": 0,
                "achromatic_count": len(achromatic_colors),
                "chromatic_count": len(chromatic_colors),
                "color_harmony_score": 0.9  # Very high harmony
            }
        
        # Check for Triadic pattern (3 chromatic colors)
        if self._is_triadic(chromatic_colors):
            return {
                "scheme_type": ColorSchemeType.TRIADIC,
                "description": "Three colors equally spaced around color wheel (120° apart)",
                "colors": color_codes,
                "hue_range": self._calculate_hue_range(chromatic_colors),
                "achromatic_count": len(achromatic_colors),
                "chromatic_count": len(chromatic_colors),
                "color_harmony_score": 0.75  # Good harmony but challenging
            }
        
        # Check for Tetradic pattern (4 chromatic colors)
        if self._is_tetradic(chromatic_colors):
            return {
                "scheme_type": ColorSchemeType.TETRADIC,
                "description": "Four colors forming two complementary pairs",
                "colors": color_codes,
                "hue_range": self._calculate_hue_range(chromatic_colors),
                "achromatic_count": len(achromatic_colors),
                "chromatic_count": len(chromatic_colors),
                "color_harmony_score": 0.65  # Challenging but dynamic
            }
        
        # Calculate hue relationships for other patterns
        hue_ranges = []
        for i in range(len(chromatic_colors)):
            for j in range(i + 1, len(chromatic_colors)):
                distance = chromatic_colors[i].hue_distance(chromatic_colors[j])
                hue_ranges.append(distance)
        
        max_hue_distance = max(hue_ranges) if hue_ranges else 0
        avg_hue_distance = sum(hue_ranges) / len(hue_ranges) if hue_ranges else 0
        
        # Determine scheme type based on hue relationships
        if max_hue_distance <= 30:
            scheme_type = ColorSchemeType.MONOCHROMATIC
            description = f"Very similar hues within {max_hue_distance:.1f}° range"
            harmony_score = 0.9
        elif max_hue_distance <= 60:
            scheme_type = ColorSchemeType.ANALOGOUS
            description = f"Adjacent hues spanning {max_hue_distance:.1f}° on color wheel"
            harmony_score = 0.8
        elif any(abs(d - 180) <= 30 for d in hue_ranges):
            scheme_type = ColorSchemeType.COMPLEMENTARY
            description = "Colors from opposite sides of color wheel"
            harmony_score = 0.7
        else:
            # Default to Tetradic for complex multi-color schemes
            scheme_type = ColorSchemeType.TETRADIC
            description = f"Multiple colors with complex relationships"
            harmony_score = max(0.3, 1.0 - (max_hue_distance - 120) / 240)
        
        return {
            "scheme_type": scheme_type,
            "description": description,
            "colors": color_codes,
            "hue_range": max_hue_distance,
            "avg_hue_distance": avg_hue_distance,
            "achromatic_count": len(achromatic_colors),
            "chromatic_count": len(chromatic_colors),
            "color_harmony_score": harmony_score
        }
    
    def _calculate_hue_range(self, colors: List[Color]) -> float:
        """Calculate hue range for a list of colors"""
        if len(colors) <= 1:
            return 0
        
        hues = [c.hue for c in colors]
        return max(hues) - min(hues)
    
    def get_usage_recommendations(self, analysis: Dict) -> Dict:
        """Updated recommendations without best_for and ulos_application"""
        scheme_type = analysis["scheme_type"]
        harmony_score = analysis.get("color_harmony_score", 0.5)
        
        recommendations = {
            ColorSchemeType.MONOCHROMATIC: {
                "primary_ratio": "60%",
                "secondary_ratio": "30%",
                "accent_ratio": "10%",
                "harmony_level": "Very High" if harmony_score > 0.85 else "High"
            },
            ColorSchemeType.ANALOGOUS: {
                "primary_ratio": "50%",
                "secondary_ratio": "30%",
                "accent_ratio": "20%",
                "harmony_level": "High" if harmony_score > 0.75 else "Medium"
            },
            ColorSchemeType.COMPLEMENTARY: {
                "primary_ratio": "70%",
                "secondary_ratio": "30%",
                "accent_ratio": "Use sparingly",
                "harmony_level": "Medium" if harmony_score > 0.65 else "Challenging"
            },
            ColorSchemeType.TRIADIC: {
                "primary_ratio": "50%",
                "secondary_ratio": "30%",
                "accent_ratio": "20%",
                "harmony_level": "Good" if harmony_score > 0.7 else "Challenging"
            },
            ColorSchemeType.TETRADIC: {
                "primary_ratio": "40%",
                "secondary_ratio": "30%",
                "accent_ratio": "30% (distributed)",
                "harmony_level": "Dynamic" if harmony_score > 0.6 else "Complex"
            },
            ColorSchemeType.ACHROMATIC: {
                "primary_ratio": "60%",
                "secondary_ratio": "40%",
                "accent_ratio": "Consider adding color",
                "harmony_level": "Neutral"
            }
        }
        
        return recommendations.get(scheme_type, {})

# Global color scheme analyzer instance
ulos_color_analyzer = UlosColorSchemeAnalyzer()

# ========== END COLOR SCHEME ANALYZER INTEGRATION ==========

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
            Anda menerima daftar warna referensi dalam format HSV (Hue, Saturation, Value) yaitu: {DB_ULOS_THREAD_COLORS}, dan warna dalam format HSV (Hue, Saturation, Value) yang dipilih oleh pengguna yaitu :{user_selected_hsv}.
            Tugas Anda adalah memberikan warna dari {DB_ULOS_THREAD_COLORS} yang paling relavan dan sejenis dengan warna yang dipilih pengguna {user_selected_hsv}.
            Output harus berupa dictionary JSON dengan struktur sebagai berikut:
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
    """Loads a grayscale image and finds its unique pixel values."""
    gray_im = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if gray_im is None:
        return None, None
    unique_values = np.unique(gray_im).tolist()
    return gray_im, unique_values

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

    if (max_hue + min_hue) == 0:
        return 0.0
        
    return (max_hue - min_hue) / (max_hue + min_hue)

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
    if actual_unique_colors - n_colors <= 1:
        return 1.0
    else:
        difference = abs(actual_unique_colors - n_colors)
        return 1 / (1 + difference)


## Coloring Problem

class UlosColoringProblem(Problem):
    """Class of problems for Ulos coloring optimization."""
    def __init__(self, unique_values, gray_image, n_colors, dict_ulos_thread_colors, user_preference_func):
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
        self.dict_ulos_thread_colors = list(dict_ulos_thread_colors.values())
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

def run_nsde(problem, termination, callback_instance):
    """Runs the NSDE (Non-dominated Sorting Differential Evolution) algorithm."""
    nsde = NSDE(pop_size=5,
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
    STAGE_COLOR_SCHEME_ANALYSIS = 94  # Added color scheme analysis stage
    STAGE_APPLY_COLORS = 95
    STAGE_SAVE_IMAGE = 98
    STAGE_COMPLETED = 100

    TOTAL_NSDE_GENERATIONS = 1
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
        
        # REFRESH COLOR ANALYZER WITH UPDATED DB DATA
        ulos_color_analyzer.refresh_colors()

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
            unique_values=unique_values,
            gray_image=gray_image,
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

        # NEW: COLOR SCHEME ANALYSIS
        update_progress(STAGE_COLOR_SCHEME_ANALYSIS)
        
        hsv_to_code_map = {tuple(v): k for k, v in DB_ULOS_THREAD_COLORS.items()}
        
        used_color_codes = []
        for hsv_value in best_color_dict.values():
            hsv_tuple = tuple(hsv_value)
            if hsv_tuple in hsv_to_code_map:
                used_color_codes.append(hsv_to_code_map[hsv_tuple])

        unique_used_color_codes = sorted(list(set(used_color_codes)))
        print("DEBUG: Used color codes:", unique_used_color_codes)
        
        # ANALYZE COLOR SCHEME
        color_scheme_analysis = ulos_color_analyzer.analyze_color_scheme(unique_used_color_codes)
        usage_recommendations = ulos_color_analyzer.get_usage_recommendations(color_scheme_analysis)
        
        print(f"DEBUG: Color Scheme Analysis: {color_scheme_analysis['scheme_type'].value}")
        print(f"DEBUG: Color Harmony Score: {color_scheme_analysis.get('color_harmony_score', 'N/A')}")

        update_progress(STAGE_APPLY_COLORS)
        colored_image_rgb = apply_coloring(gray_image, best_color_dict)

        update_progress(STAGE_SAVE_IMAGE)
        relative_output_path = save_colored_image(colored_image_rgb, ulos_type)
        
        # ENHANCED Final success update with color scheme analysis
        final_result = {
            'progress': STAGE_COMPLETED,
            'status': 'Completed',
            'colored_image_url': relative_output_path,
            'unique_used_color_codes': unique_used_color_codes,
            # NEW: Color scheme analysis results
            'color_scheme_analysis': {
                'scheme_type': color_scheme_analysis['scheme_type'].value,
                'description': color_scheme_analysis['description'],
                'hue_range': color_scheme_analysis.get('hue_range', 0),
                'color_harmony_score': color_scheme_analysis.get('color_harmony_score', 0),
                'achromatic_count': color_scheme_analysis.get('achromatic_count', 0),
                'chromatic_count': color_scheme_analysis.get('chromatic_count', 0)
            },
            'usage_recommendations': {
                'best_for': usage_recommendations.get('best_for', ''),
                'ulos_application': usage_recommendations.get('ulos_application', ''),
                'harmony_level': usage_recommendations.get('harmony_level', ''),
                'primary_ratio': usage_recommendations.get('primary_ratio', ''),
                'secondary_ratio': usage_recommendations.get('secondary_ratio', ''),
                'accent_ratio': usage_recommendations.get('accent_ratio', '')
            },
            # Optimization scores
            'optimization_scores': {
                'michaelson_contrast': float(-best_scores[0]),
                'rms_contrast': float(-best_scores[1]),
                'colorfulness': float(-best_scores[2]),
                'optimal_unique_colors': float(-best_scores[3]),
                'user_preference_match': float(-best_scores[4])
            }
        }
        cache.set(task_id, final_result, timeout=3600)
        return relative_output_path, unique_used_color_codes, color_scheme_analysis, usage_recommendations

    except Exception as e:
        print(f"ERROR in main_coloring_process: {str(e)}")
        cache.set(task_id, {
            'progress': STAGE_COMPLETED,
            'status': 'Error',
            'error_message': str(e)
        }, timeout=3600)
        return None, None, None, None

# UTILITY FUNCTIONS FOR FRONTEND INTEGRATION

def get_color_scheme_preview(color_codes_list: List[str]) -> Dict:
    """
    Utility function to get color scheme analysis without running full optimization.
    Useful for frontend preview before starting the optimization process.
    """
    try:
        # Ensure analyzer has latest data
        ulos_color_analyzer.refresh_colors()
        
        # Analyze the color scheme
        analysis = ulos_color_analyzer.analyze_color_scheme(color_codes_list)
        recommendations = ulos_color_analyzer.get_usage_recommendations(analysis)
        
        return {
            'success': True,
            'scheme_type': analysis['scheme_type'].value,
            'description': analysis['description'],
            'harmony_score': analysis.get('color_harmony_score', 0),
            'recommendations': recommendations,
            'color_details': {
                code: {
                    'hue': ulos_color_analyzer.colors[code].hue,
                    'saturation': ulos_color_analyzer.colors[code].saturation,
                    'value': ulos_color_analyzer.colors[code].value
                } for code in color_codes_list if code in ulos_color_analyzer.colors
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_similar_colors_suggestion(primary_color_code: str, count: int = 5) -> Dict:
    """
    Get similar color suggestions based on a primary color.
    Useful for frontend color picker assistance.
    """
    try:
        ulos_color_analyzer.refresh_colors()
        similar_colors = ulos_color_analyzer.find_similar_colors(primary_color_code, count)
        
        return {
            'success': True,
            'primary_color': primary_color_code,
            'similar_colors': similar_colors,
            'color_details': {
                code: {
                    'hue': ulos_color_analyzer.colors[code].hue,
                    'saturation': ulos_color_analyzer.colors[code].saturation,
                    'value': ulos_color_analyzer.colors[code].value
                } for code in [primary_color_code] + similar_colors if code in ulos_color_analyzer.colors
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == '__main__':
    pass