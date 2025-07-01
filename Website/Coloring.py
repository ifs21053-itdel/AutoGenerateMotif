import sys                    # Modul standar untuk manipulasi sistem (argumen, path, dll.)
import os                     # Modul standar untuk operasi file dan direktori
import json                   # Untuk parsing dan penyimpanan data JSON
import numpy as np            # Library numerik untuk array dan komputasi ilmiah
import cv2                    # OpenCV untuk pengolahan citra dan video
from pymoo.core.problem import Problem                   # Class untuk mendefinisikan masalah optimasi
from pymoode.algorithms import NSDE                      # Algoritma NSDE dari pustaka Pymoode
from pymoode.survival import RankAndCrowding             # Strategi survival berdasarkan ranking dan crowding
from skimage.color import hsv2rgb                        # Konversi warna dari HSV ke RGB
from openai import OpenAI                                # Klien API OpenAI untuk memanggil LLM
import matplotlib.pyplot as plt                          # Library visualisasi (grafik, plot)
from pymoo.operators.mutation.pm import PolynomialMutation     # Operator mutasi polinomial (untuk evolusi)
from pymoo.operators.repair.rounding import RoundingRepair     # Operator pembulatan nilai solusi agar valid
from pymoo.optimize import minimize                            # Fungsi utama untuk proses optimasi
from pymoo.termination import get_termination                  # Untuk mendefinisikan kondisi berhenti algoritma
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting  # Untuk sorting solusi non-dominated
from django.conf import settings                         # Akses konfigurasi dari Django
from django.core.cache import cache                      # Mekanisme cache (penyimpanan sementara) di Django
import importlib.util                                     # Untuk memuat modul eksternal secara dinamis
from pymoo.core.callback import Callback                 # Untuk mendefinisikan fungsi callback saat optimasi
from typing import List, Dict                            # Untuk anotasi tipe data list dan dict
from dataclasses import dataclass                        # Untuk membuat class data secara ringkas
from enum import Enum                                    # Untuk membuat enumerasi (daftar nilai tetap)
from Website.models import UlosColorThread, UlosCharacteristic      # Import Django models

# Load API key
key_file_path = os.path.join(
    settings.BASE_DIR,
    'static',
    'ColoringFile',
    'deepseek_api.txt'
    )
with open(key_file_path, "r") as key_file:
    api_key = key_file.readline().strip()  # Simpan API key setelah dibaca

# Variabel global untuk menyimpan data ulos dari database
DB_ULOS_CHARACTERISTICS = {}
DB_ULOS_THREAD_COLORS = {}

def load_ulos_data_from_db():
    """Loads Ulos characteristics and thread colors from the Django database."""
    global DB_ULOS_CHARACTERISTICS, DB_ULOS_THREAD_COLORS

    try:
        # Ambil semua data karakteristik ulos dari DB
        characteristics = UlosCharacteristic.objects.all()
        for char in characteristics:
            DB_ULOS_CHARACTERISTICS[char.NAME] = {
                "garis": char.garis,
                "pola": char.pola,
                "warna_dominasi": char.warna_dominasi,
                "warna_aksen": char.warna_aksen,
                "kontras_warna": char.kontras_warna,
            }

        # Ambil semua data warna benang ulos dan konversi ke format HSV
        colors = UlosColorThread.objects.all()              # Ambil semua data warna benang dari database
        for color in colors:                               
            h, s, v = map(int, color.hsv.split(','))        # Pisahkan string HSV jadi tiga angka: h, s, v
            DB_ULOS_THREAD_COLORS[color.CODE] = [h, s, v]   # Simpan ke dict global dengan kode warna sebagai kunci
    except Exception as e:
        DB_ULOS_CHARACTERISTICS = {}
        DB_ULOS_THREAD_COLORS = {}

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
        self.hue = self.hue % 360  # Normalisasi hue ke rentang 0-360°

    
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
        self.colors = {}     # Simpan warna dari DB
        self._load_colors_from_db()     # Load saat inisialisasi
    
    def _load_colors_from_db(self):
        """Load colors from existing DB_ULOS_THREAD_COLORS"""
        for code, hsv_values in DB_ULOS_THREAD_COLORS.items():
            h, s, v = hsv_values
            self.colors[code] = Color(code, h, s, v)
    
    def refresh_colors(self):
        """Refresh colors when DB data is updated"""
        self._load_colors_from_db()
    
    def find_similar_colors(self, primary_color_code: str, count: int = 3) -> List[str]:
        """Find similar colors based on hue, saturation, and value"""
        if primary_color_code not in self.colors:
            return []
        
        primary = self.colors[primary_color_code]
        similarities = []
        
        for code, color in self.colors.items():
            if code == primary_color_code:
                continue
            
            # # Hitung skor bobot kemiripan
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
        similarities.sort(key=lambda x: x[1], reverse=True)     # Urutkan berdasarkan skor
        return [code for code, _ in similarities[:count]]       # Ambil N warna teratas
    
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
                "hue_range": 0
            }
        
        # Analyze chromatic colors only for pattern detection
        if len(chromatic_colors) == 1:
            return {
                "scheme_type": ColorSchemeType.MONOCHROMATIC,
                "description": "Single color with neutral variations",
                "colors": color_codes,
                "hue_range": 0,
                "achromatic_count": len(achromatic_colors),
                "chromatic_count": len(chromatic_colors)
            }
        
        # Check for Triadic pattern (3 chromatic colors)
        if self._is_triadic(chromatic_colors):
            return {
                "scheme_type": ColorSchemeType.TRIADIC,
                "description": "Three colors equally spaced around color wheel (120° apart)",
                "colors": color_codes,
                "hue_range": self._calculate_hue_range(chromatic_colors),
                "achromatic_count": len(achromatic_colors),
                "chromatic_count": len(chromatic_colors)
            }
        
        # Check for Tetradic pattern (4 chromatic colors)
        if self._is_tetradic(chromatic_colors):
            return {
                "scheme_type": ColorSchemeType.TETRADIC,
                "description": "Four colors forming two complementary pairs",
                "colors": color_codes,
                "hue_range": self._calculate_hue_range(chromatic_colors),
                "achromatic_count": len(achromatic_colors),
                "chromatic_count": len(chromatic_colors)
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
        elif max_hue_distance <= 60:
            scheme_type = ColorSchemeType.ANALOGOUS
            description = f"Adjacent hues spanning {max_hue_distance:.1f}° on color wheel"
        elif any(abs(d - 180) <= 30 for d in hue_ranges):
            scheme_type = ColorSchemeType.COMPLEMENTARY
            description = "Colors from opposite sides of color wheel"
        else:
            # Default to Tetradic for complex multi-color schemes
            scheme_type = ColorSchemeType.TETRADIC
            description = f"Multiple colors with complex relationships"
        
        return {
            "scheme_type": scheme_type,
            "description": description,
            "colors": color_codes,
            "hue_range": max_hue_distance,
            "avg_hue_distance": avg_hue_distance,
            "achromatic_count": len(achromatic_colors),
            "chromatic_count": len(chromatic_colors)
        }
    
    def _calculate_hue_range(self, colors: List[Color]) -> float:
        """Calculate hue range for a list of colors"""
        if len(colors) <= 1:
            return 0
        
        hues = [c.hue for c in colors]
        return max(hues) - min(hues)

# Global color scheme analyzer instance
ulos_color_analyzer = UlosColorSchemeAnalyzer()


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

    # Inisialisasi klien DeepSeek
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    # Ambil nilai HSV dari warna yang dipilih pengguna
    list_colors_hsv = [DB_ULOS_THREAD_COLORS[code] for code in ulos_selected_color_codes]

    # Kirim prompt ke LLM untuk menghasilkan kode Python fungsi objektif
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a Senior Programmer."},
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
            Hasilkan hanya kode program Python lengkap yang dapat langsung dieksekusi,tidak tanpa teks penjelasan, tanpa tanda kutip balik (```), tidak error dan tanpa karakter atau teks tambahan apapun di awal atau akhir. Pastikan semua kurung dan tanda baca lainnya tertutup dengan benar."""
            },
        ],
    )
    # Ambil isi kode program dari respons
    response_content = response.choices[0].message.content      # Ambil isi respons (teks kode Python) dari objek respons API
    return response_content.strip()                             # Hapus spasi kosong di awal/akhir lalu kembalikan teks bersih

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
            Anda menerima daftar warna dalam format HSV (Hue, Saturation, Value) yaitu: {DB_ULOS_THREAD_COLORS}, dan warna dalam format HSV (Hue, Saturation, Value) yang dipilih oleh pengguna yaitu :{user_selected_hsv}.
            Berikan warna yang sesuai dengan referensi pengguna dari daftar warna yang diberikan.
            Output harus berupa dictionary JSON dengan struktur sebagai berikut:
            - Key: berisi kode warna yang sesuai dengan referensi pengguna
            - Value: berisi warna HSV yang sesuai dengan referensi pengguna
            Pastikan:
            1. Format kode dan value warna dikembalikan dalam daftar seperti pada {DB_ULOS_THREAD_COLORS}
            2. Satu kode hanya mengandung satu value dan key
            3. Output harus valid menggunakan format JSON
            berikan daftar warna saja, jangan tambahkan keterangan.
            """
            },
        ],
    )
    response_content = response.choices[0].message.content        # Ambil isi respons (teks kode Python) dari objek respons API
    return json.loads(response_content[response_content.find('{') : response_content.rfind('}') + 1])

## Utils

def get_unique_colors(image_path):
    """Loads a grayscale image and finds its unique pixel values."""
    gray_im = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if gray_im is None:
        return None, None
    unique_values = np.unique(gray_im).tolist()     # Mengambil semua nilai piksel unik dari gambar grayscale
    return gray_im, unique_values

def apply_coloring(gray_image, color_dict):
    """Mewarnai citra grayscale berdasarkan mapping gray_value ke HSV."""
    # Membuat citra kosong dengan 3 channel (RGB), ukuran sama dengan gray_image
    color_image = np.zeros((gray_image.shape[0], gray_image.shape[1], 3), dtype=np.uint8)

    # Iterasi untuk setiap gray value dan warna HSV yang diberikan dalam dictionary
    for gray_value, hsv in color_dict.items():
        # Normalisasi nilai HSV agar sesuai dengan rentang yang digunakan dalam konversi warna
        hsv_normalized = np.array([[hsv[0] / 360.0,
                                     hsv[1] / 100.0,
                                     hsv[2] / 100.0]], dtype=np.float32)
         # Konversi HSV (normalized) ke RGB → hasilnya skala 0–1, lalu dikali 255 agar skala 0–255
        rgb_color = hsv2rgb(hsv_normalized.reshape(1, 1, 3)).reshape(3) * 255
         # Terapkan warna RGB tersebut ke semua piksel di gray_image yang memiliki nilai gray_value
        color_image[gray_image == int(gray_value)] = rgb_color.astype(np.uint8)
    return color_image

def display_colored_image(colored_image):
    """Displays the colored image using Matplotlib."""
    plt.imshow(colored_image)
    plt.axis('off')
    plt.show()

def save_colored_image(color_image, ulos_type):
    """Menyimpan citra berwarna ke direktori output dan mengembalikan path relatifnya."""

    # Tentukan direktori penyimpanan (dalam folder static/ColoringFile/output/)
    output_dir = os.path.join(settings.BASE_DIR, 'static', 'ColoringFile', 'output')

    # Buat nama file berdasarkan tipe Ulos
    output_filename = f"colored_ulos_{ulos_type}.png"
    output_image_path = os.path.join(output_dir, output_filename)

    # OpenCV menyimpan gambar dalam format BGR, maka perlu konversi dari RGB
    colored_image_bgr = cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)
    # Simpan gambar ke disk dalam format PNG
    cv2.imwrite(output_image_path, colored_image_bgr)

    # Menghasilkan path relatif yang digunakan di frontend atau web
    relative_output_path = os.path.join('ColoringFile', 'output', output_filename).replace(os.sep, '/')

    return relative_output_path


## Objective Functions

def calculate_michaelson_contrast(hsv_image):
    """Menghitung kontras Michaelson dari citra HSV."""

    # Ambil channel Hue (komponen warna), lalu normalisasi dari 0–179 menjadi 0–1
    hue_channel = hsv_image[:, :, 0] / 179.0

    # Hitung nilai hue minimum dan maksimum dari seluruh gambar
    min_hue = np.min(hue_channel)
    max_hue = np.max(hue_channel)

    # Jika total dari min + max = 0 (menghindari pembagian nol)
    if (max_hue + min_hue) == 0:
        return 0.0

    # Rumus Michaelson Contrast: (Imax - Imin) / (Imax + Imin)
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
    """Menghitung tingkat kewarnaan (colorfulness) dari citra HSV."""

    # Konversi HSV ke RGB agar bisa dihitung per channel warna
    img_rgb = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2RGB)

    # Pisahkan channel RGB
    red, green, blue = cv2.split(img_rgb)

    # Hitung perbedaan antara saluran warna
    rg = red - green                         # Selisih antara Merah dan Hijau
    yb = 0.5 * (red + green) - blue          # Kombinasi Merah-Hijau dikurangi Biru

    # Hitung rata-rata dan standar deviasi dari perbedaan warna
    mean_rg = np.mean(rg)
    mean_yb = np.mean(yb)
    std_rg = np.std(rg)
    std_yb = np.std(yb)

    # Rumus colorfulness
    colorfulness = np.sqrt(std_rg**2 + std_yb**2) + 0.3 * np.sqrt(mean_rg**2 + mean_yb**2)

    return colorfulness


def calculate_optimal_unique_colors(hsv_image, n_colors):
    """
    Mengukur kesesuaian jumlah warna unik pada gambar terhadap jumlah target.
    """

    # Hitung kombinasi warna HSV unik dari seluruh piksel gambar
    unique_hsv_combinations = np.unique(hsv_image.reshape(-1, hsv_image.shape[2]), axis=0)
    actual_unique_colors = len(unique_hsv_combinations)

    # Jika jumlah aktual hampir sama dengan target (selisih 0 atau 1), beri skor maksimal 1.0
    if actual_unique_colors - n_colors <= 1:
        return 1.0
    else:
        # Semakin jauh selisihnya dari target, semakin kecil skornya
        difference = abs(actual_unique_colors - n_colors)
        return 1 / (1 + difference)


## Coloring Problem

class UlosColoringProblem(Problem):
    """Class of problems for Ulos coloring optimization."""
    def __init__(self, unique_values, gray_image, n_colors, dict_ulos_thread_colors, user_preference_func):
        total_unique_values = len(unique_values)

        # Inisialisasi parent class Problem dengan parameter:
        # - n_var = jumlah variabel desain (1 warna per nilai gray unik)
        # - n_obj = 5 fungsi objektif (kontras, kewarnaan, dll)
        # - n_constr = tidak ada kendala eksplisit
        # - xl dan xu = batas bawah dan atas masing-masing variabel
        super().__init__(n_var=total_unique_values,
                         n_obj=5,
                         n_constr=0,
                         xl=np.array([0] * total_unique_values),        # semua indeks minimal 0
                         xu=np.array([len(dict_ulos_thread_colors.values())]
                                     * total_unique_values))

        # Simpan parameter yang dibutuhkan untuk evaluasi
        self.unique_values = unique_values
        self.gray_image = gray_image
        self.total_unique_values = total_unique_values
        self.dict_ulos_thread_colors = list(dict_ulos_thread_colors.values())
        self.calculate_user_color_preferences = user_preference_func


    def _evaluate(self, x, out, *args, **kwargs):
        """Evaluasi seluruh populasi (x) dan menghasilkan nilai untuk setiap fungsi objektif."""

        # Buat dictionary: index → warna HSV
        indexed_dict = {index: value for index, value in enumerate(self.dict_ulos_thread_colors)}

        F_values = []  # Untuk menyimpan nilai-nilai fungsi objektif dari setiap individu/solusi

        # Iterasi semua individu dalam populasi (x)
        for individual in x:

            # Konversi representasi genetik ke daftar warna HSV berdasarkan indeks
            list_generated_unique_hsv_values = [indexed_dict[int(i)] for i in individual.flatten()]

            # Buat representasi HSV dari grayscale untuk digunakan sebagai key
            list_original_unique_hsv_values = [tuple([i, i, i]) for i in self.unique_values]

            # Buat mapping grayscale → warna hasil evolusi
            color_mappings = dict(zip(list_original_unique_hsv_values, list_generated_unique_hsv_values))

            # Buat array HSV citra dari citra grayscale (3 channel)
            modified_image = np.repeat(self.gray_image[:, :, np.newaxis], 3, axis=2)

            # Aplikasikan warna ke setiap piksel berdasarkan nilai grayscale
            for gray_value, color_value in color_mappings.items():
                scalar_gray_value = gray_value[0]  # karena (i, i, i), cukup ambil satu nilai

                color_value_array = np.array(color_value)[np.newaxis, np.newaxis, :]  # ubah ke (1, 1, 3)

                # Ganti semua piksel yang memiliki nilai grayscale tertentu dengan warna HSV hasil evolusi
                modified_image[self.gray_image == scalar_gray_value] = color_value_array

            # Hitung nilai fungsi objektif untuk gambar yang telah diwarnai
            f1 = calculate_michaelson_contrast(modified_image)                     # Kontras warna (hue)
            f2 = calculate_rms_contrast(modified_image)                            # Kontras luminansi (terang-gelap)
            f3 = calculate_colorfulness(modified_image)                            # Tingkat kewarnaan
            f4 = calculate_optimal_unique_colors(modified_image, self.total_unique_values)  # Jumlah warna unik ideal
            f5 = self.calculate_user_color_preferences(modified_image)             # Preferensi pengguna (evaluasi khusus)

            # Simpan semua nilai fungsi objektif (diberi tanda minus karena akan diminimalkan oleh algoritma)
            F_values.append([-f1, -f2, -f3, -f4, -f5])

        # Masukkan hasil evaluasi ke dalam struktur keluaran (output) standar `pymoo`
        out["F"] = np.array(F_values)


# Progress Callback Class 

class NSDEProgressReporter(Callback):
    """
    Callback untuk PyMoo yang hanya melaporkan generasi NSDE saat ini.
    Fungsi utama (main_coloring_process) akan menangani kalkulasi progres keseluruhan.
    """

    def __init__(self, update_main_progress_func):
        """
        Inisialisasi objek callback.
        Parameter:
        - update_main_progress_func: fungsi eksternal (biasanya dari main process)
          yang akan dipanggil setiap generasi untuk memperbarui status/progres.
        """
        super().__init__()  # Memanggil konstruktor dari kelas induk Callback
        self.update_main_progress_func = update_main_progress_func  # Simpan referensi fungsi progres eksternal

    def notify(self, algorithm):
        """
        Dipanggil secara otomatis oleh PyMoo setiap generasi selesai dijalankan.
        Parameter:
        - algorithm: objek algoritma evolusi yang sedang berjalan (berisi informasi generasi saat ini).
        """
        current_gen = algorithm.n_gen  # Ambil nomor generasi saat ini dari NSDE
        self.update_main_progress_func(current_gen)  # Panggil fungsi eksternal untuk laporkan progres


# End Progress Callback Class 


## NSDE Optimization

def run_nsde(problem, termination, callback_instance):
    """
    Menjalankan algoritma NSDE (Non-dominated Sorting Differential Evolution)
    untuk menyelesaikan masalah optimasi multi-objektif.

    Parameter:
    - problem: objek kelas turunan dari pymoo.core.Problem (misalnya UlosColoringProblem)
    - termination: objek termination untuk menghentikan algoritma (misalnya setelah 100 generasi)
    - callback_instance: callback (seperti NSDEProgressReporter) untuk melacak progres generasi

    Mengembalikan:
    - result: hasil akhir dari optimisasi, termasuk solusi terbaik, pareto front, dsb.
    """

    # Inisialisasi algoritma NSDE dengan parameter-parameter tertentu
    nsde = NSDE(
        pop_size=5,                       # Ukuran populasi = 5 individu
        variant="DE/rand/1/bin",         # Variasi strategi DE: random/1/binomial
        CR=0.7,                           # Crossover rate = 0.7 (probabilitas recombination)
        F=0.85,                           # Faktor diferensiasi = 0.85 (penguat mutasi)
        de_repair="bounce-back",         # Strategi repair jika individu keluar dari batas
        survival=RankAndCrowding(        # Mekanisme survival berdasarkan ranking & crowding distance
            crowding_func="cd"           # Menggunakan crowding distance sebagai metrik sebaran
        )
    )

    # Jalankan algoritma optimasi dengan fungsi minimize dari PyMoo
    result = minimize(
        problem,                  # Masalah optimasi yang akan diselesaikan
        nsde,                     # Algoritma evolusi yang digunakan (NSDE)
        termination,              # Kriteria penghentian (jumlah generasi, waktu, dsb)
        seed=42,                  # Seed untuk hasil yang konsisten (reproducibility)
        verbose=True,             # Tampilkan log proses optimasi di konsol
        callback=callback_instance  # Objek callback untuk memantau progres tiap generasi
    )

    return result  # Kembalikan hasil akhir optimasi (tipe: pymoo.optimize.MinimizationResult)


def get_best_individual(result, unique_values, available_colors):
    """
    Mengambil individu terbaik dari hasil optimasi NSDE dengan normalisasi nilai objektif.

    Parameter:
    - result: hasil dari pymoo.optimize.minimize (berisi populasi akhir, nilai objektif, dll)
    - unique_values: daftar nilai unik dari gambar grayscale
    - available_colors: daftar warna HSV yang tersedia (urutan sesuai indeks kromosom)

    Return:
    - best_individual: representasi kromosom individu terbaik (indeks warna)
    - best_color_dict_converted: dictionary grayscale → HSV (dalam format int)
    - best_scores: nilai objektif asli dari individu terbaik (belum dinormalisasi)
    """

    # Ambil semua nilai fitness dari hasil NSDE (dalam bentuk negatif karena minimisasi)
    pareto_front = result.F
    # Konversi ke nilai fungsi objektif asli (positif)
    objective_values = -pareto_front

    # Normalisasi setiap fungsi objektif ke rentang [0, 1]
    normalized_values = np.zeros_like(objective_values)
    for i in range(objective_values.shape[1]):
        col = objective_values[:, i]
        min_val, max_val = np.min(col), np.max(col)

        if max_val == min_val:
            # Jika semua nilai sama, semua dianggap 1 (maksimum kontribusi)
            normalized_values[:, i] = 1.0
        else:
            # (x - min) / (max - min)
            normalized_values[:, i] = (col - min_val) / (max_val - min_val)

    # Jumlahkan skor normalisasi tiap individu
    total_scores = np.sum(normalized_values, axis=1)

    # Pilih individu dengan skor total tertinggi
    best_index = np.argmax(total_scores)

    # Ambil kromosom terbaik
    best_individual = result.X[best_index].astype(int)

    # Ambil skor asli (belum dinormalisasi)
    best_scores = pareto_front[best_index]

    # Buat dictionary hasil mapping grayscale → HSV
    best_color_dict_converted = {
        int(k): [int(available_colors[v][0]),
                 int(available_colors[v][1]),
                 int(available_colors[v][2])]
        for k, v in zip(unique_values, best_individual)
    }

    return best_individual, best_color_dict_converted, best_scores


def main_coloring_process(ulos_type_input, ulos_selected_color_codes_input, base_image_path, task_id):
    # Inisialisasi konstanta tahap-tahap progres pewarnaan
    STAGE_START = 1
    STAGE_LOAD_DB = 5
    STAGE_GEN_OBJ_FUNC = 10
    STAGE_IMPORT_OBJ_FUNC = 15
    STAGE_FETCH_COLORS = 20
    STAGE_NSDE_OPTIMIZATION_START = 25
    STAGE_NSDE_OPTIMIZATION_END = 90
    STAGE_PROCESS_RESULTS = 92
    STAGE_COLOR_SCHEME_ANALYSIS = 94
    STAGE_APPLY_COLORS = 95
    STAGE_SAVE_IMAGE = 98
    STAGE_COMPLETED = 100

    # Total generasi NSDE (dapat diatur)
    TOTAL_NSDE_GENERATIONS = 2
    current_nsde_generation = 0  # Variabel untuk menyimpan progres generasi saat ini

    # Fungsi untuk memperbarui progres utama ke cache (dapat dibaca klien)
    def update_progress(progress):
        cache.set(task_id, {'progress': progress}, timeout=3600)

    # Fungsi yang dipanggil oleh NSDE callback untuk memperbarui progres berdasarkan generasi
    def update_nsde_progress_in_main(gen):
        nonlocal current_nsde_generation  # Referensi ke variabel luar fungsi
        current_nsde_generation = gen  # Simpan generasi saat ini

        nsde_progress_range = STAGE_NSDE_OPTIMIZATION_END - STAGE_NSDE_OPTIMIZATION_START
        if TOTAL_NSDE_GENERATIONS > 0:
            progress_within_nsde_range = (current_nsde_generation / TOTAL_NSDE_GENERATIONS) * nsde_progress_range
        else:
            progress_within_nsde_range = nsde_progress_range  # Jika tidak ada generasi, anggap sudah selesai

        total_progress = int(STAGE_NSDE_OPTIMIZATION_START + progress_within_nsde_range)
        update_progress(total_progress)  # Kirim progres gabungan ke cache

    try:
        update_progress(STAGE_START)  # Proses dimulai
        update_progress(STAGE_LOAD_DB)  # Tahap load data dari DB
        load_ulos_data_from_db()  # Ambil data ulos dan warna dari database

        ulos_color_analyzer.refresh_colors()  # Sinkronkan ulang data warna

        # Simpan input dari pengguna
        ulos_type = ulos_type_input
        ulos_colors_codes = ulos_selected_color_codes_input
        n_colors = len(ulos_colors_codes)  # Hitung jumlah warna yang dipilih user

        update_progress(STAGE_GEN_OBJ_FUNC)  # Tahap pembuatan fungsi objektif

        # Buat kode Python fungsi objektif berdasarkan karakteristik ulos & warna user
        objective_function_code = create_custom_objective_function(ulos_type, api_key, ulos_colors_codes)

        # Simpan kode ke file sementara
        custom_obj_dir = os.path.join(settings.BASE_DIR, 'static', 'ColoringFile')
        os.makedirs(custom_obj_dir, exist_ok=True)  # Pastikan folder ada
        temp_objective_file_path = os.path.join(custom_obj_dir, "custom_objective_function.py")
        with open(temp_objective_file_path, "w", encoding='utf-8') as file:
            file.write(objective_function_code)  # Tulis isi fungsi ke file

        update_progress(STAGE_IMPORT_OBJ_FUNC)  # Tahap import fungsi objektif

        # Import fungsi objektif dari file secara dinamis
        spec = importlib.util.spec_from_file_location("custom_obj_func_module", temp_objective_file_path)
        custom_obj_func_module = importlib.util.module_from_spec(spec)
        sys.modules["custom_obj_func_module"] = custom_obj_func_module
        spec.loader.exec_module(custom_obj_func_module)

        # Ambil fungsi calculate_user_color_preferences dari modul
        calculate_user_color_preferences_func = custom_obj_func_module.calculate_user_color_preferences
        print("DEBUG: Custom objective function generated and imported successfully.")

        update_progress(STAGE_FETCH_COLORS)  # Tahap mengambil warna dari LLM

        dict_ulos_thread_colors = {}  # Kamus semua warna yang bisa digunakan
        recommended_colors_dict = user_color_threads(api_key, ulos_colors_codes)  # Panggil LLM untuk rekomendasi warna
        dict_ulos_thread_colors.update(recommended_colors_dict)

        # Tambahkan warna dari DB yang juga dipilih oleh user
        dict_ulos_thread_colors.update({
            code: DB_ULOS_THREAD_COLORS[code]
            for code in ulos_colors_codes & DB_ULOS_THREAD_COLORS.keys()
        })
        print(f"DEBUG: Recommended Colors Dictionary: {recommended_colors_dict}")

        # Ambil gambar grayscale dan daftar nilai unik piksel
        gray_image, unique_values = get_unique_colors(base_image_path)
        if gray_image is None or unique_values is None:
            update_progress(STAGE_COMPLETED)
            return None, None  # Jika gambar tidak valid, hentikan proses

        # Bentuk problem pewarnaan untuk dioptimasi oleh NSDE
        problem = UlosColoringProblem(
            unique_values=unique_values,
            gray_image=gray_image,
            n_colors=n_colors,
            dict_ulos_thread_colors=dict_ulos_thread_colors,
            user_preference_func=calculate_user_color_preferences_func
        )
        print("DEBUG: UlosColoringProblem defined successfully.")

        # Inisialisasi algoritma NSDE
        termination = get_termination("n_gen", TOTAL_NSDE_GENERATIONS)
        nsde_reporter_callback = NSDEProgressReporter(update_nsde_progress_in_main)

        print("DEBUG: Running NSDE optimization...")
        update_progress(STAGE_NSDE_OPTIMIZATION_START)

        # Jalankan optimasi NSDE
        result = run_nsde(problem, termination, nsde_reporter_callback)

        update_progress(STAGE_NSDE_OPTIMIZATION_END)

        # Ambil hasil terbaik dari NSDE
        update_progress(STAGE_PROCESS_RESULTS)
        best_individual, best_color_dict, best_scores = get_best_individual(
            result, unique_values, list(dict_ulos_thread_colors.values())
        )
        print(f"DEBUG: Best individual (color indices): {best_individual}")
        print(f"DEBUG: Best scores (objectives): {best_scores}")
        print(f"DEBUG: Final color mapping: {best_color_dict}")

        # Analisis skema warna dari hasil terbaik
        update_progress(STAGE_COLOR_SCHEME_ANALYSIS)

        # Konversi dari HSV hasil optimasi ke kode warna thread
        hsv_to_code_map = {tuple(v): k for k, v in DB_ULOS_THREAD_COLORS.items()}
        used_color_codes = []
        for hsv_value in best_color_dict.values():
            hsv_tuple = tuple(hsv_value)
            if hsv_tuple in hsv_to_code_map:
                used_color_codes.append(hsv_to_code_map[hsv_tuple])

        unique_used_color_codes = sorted(list(set(used_color_codes)))  # Ambil kode warna unik yang digunakan
        print("DEBUG: Used color codes:", unique_used_color_codes)

        # Jalankan analisis skema warna (monokromatik, komplementer, dll.)
        color_scheme_analysis = ulos_color_analyzer.analyze_color_scheme(unique_used_color_codes)
        print(f"DEBUG: Color Scheme Analysis: {color_scheme_analysis['scheme_type'].value}")

        # Terapkan warna hasil optimasi ke citra grayscale
        update_progress(STAGE_APPLY_COLORS)
        colored_image_rgb = apply_coloring(gray_image, best_color_dict)

        # Simpan hasil gambar ke file dan ambil path relatifnya
        update_progress(STAGE_SAVE_IMAGE)
        relative_output_path = save_colored_image(colored_image_rgb, ulos_type)

        # Simpan hasil akhir ke cache, termasuk informasi analisis dan skor
        final_result = {
            'progress': STAGE_COMPLETED,
            'status': 'Completed',
            'colored_image_url': relative_output_path,
            'unique_used_color_codes': unique_used_color_codes,
            'color_scheme_analysis': {
                'scheme_type': color_scheme_analysis['scheme_type'].value,
                'description': color_scheme_analysis['description'],
                'hue_range': color_scheme_analysis.get('hue_range', 0),
                'achromatic_count': color_scheme_analysis.get('achromatic_count', 0),
                'chromatic_count': color_scheme_analysis.get('chromatic_count', 0)
            },
            'optimization_scores': {
                'michaelson_contrast': float(-best_scores[0]),
                'rms_contrast': float(-best_scores[1]),
                'colorfulness': float(-best_scores[2]),
                'optimal_unique_colors': float(-best_scores[3]),
                'user_preference_match': float(-best_scores[4])
            }
        }
        cache.set(task_id, final_result, timeout=3600)  # Simpan hasil akhir ke cache
        return relative_output_path, unique_used_color_codes, color_scheme_analysis

    except Exception as e:
        # Tangkap dan laporkan error jika ada
        print(f"ERROR in main_coloring_process: {str(e)}")
        cache.set(task_id, {
            'progress': STAGE_COMPLETED,
            'status': 'Error',
            'error_message': str(e)
        }, timeout=3600)
        return None, None, None, None

if __name__ == '__main__':
    pass