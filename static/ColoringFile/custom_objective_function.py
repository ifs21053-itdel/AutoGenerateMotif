import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Preferensi pengguna dalam HSV (Hue 0-360, Saturation 0-100, Value 0-100)
    user_preferences = np.array([[0, 0, 0], [140, 100, 60], [18, 75, 44]], dtype=np.int32)
    
    # Ekstrak kombinasi unik HSV dari gambar
    unique_colors = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Konversi ke format yang sesuai (Hue 0-360, Saturation 0-100, Value 0-100)
    # Perhatikan bahwa OpenCV HSV: H(0-179), S(0-255), V(0-255)
    converted_colors = np.empty_like(unique_colors, dtype=np.int32)
    converted_colors[:, 0] = (unique_colors[:, 0].astype(np.int32) * 2) % 360  # Hue to 0-360
    converted_colors[:, 1] = np.round(unique_colors[:, 1].astype(np.float32) / 255 * 100).astype(np.int32)  # S to 0-100
    converted_colors[:, 2] = np.round(unique_colors[:, 2].astype(np.float32) / 255 * 100).astype(np.int32)  # V to 0-100
    
    # Hitung fitness berdasarkan kesesuaian dengan preferensi pengguna
    fitness = 0.0
    for pref in user_preferences:
        min_dist = float('inf')
        for color in converted_colors:
            # Hitung jarak Euclidean dengan normalisasi komponen
            hue_diff = min(abs(color[0] - pref[0]), 360 - abs(color[0] - pref[0])) / 180.0
            sat_diff = abs(color[1] - pref[1]) / 100.0
            val_diff = abs(color[2] - pref[2]) / 100.0
            dist = np.sqrt(hue_diff**2 + sat_diff**2 + val_diff**2)
            if dist < min_dist:
                min_dist = dist
        fitness += (1.0 - min_dist)
    
    # Normalisasi fitness
    fitness /= len(user_preferences)
    return fitness