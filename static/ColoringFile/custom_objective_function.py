import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Preferensi pengguna dalam HSV (H: 0-360, S: 0-100, V: 0-100)
    user_preferences = np.array([[0, 0, 0], [0, 0, 100]], dtype=np.int32)
    
    # Konversi image_hsv ke int32 dan adjust hue ke 0-360
    hsv_values = image_hsv.astype(np.int32)
    hsv_values[..., 0] = (hsv_values[..., 0] * 2) % 360  # Konversi hue 0-179 ke 0-360
    hsv_values[..., 1] = np.round(hsv_values[..., 1] * 100 / 255).astype(np.int32)  # Konversi saturation ke 0-100
    hsv_values[..., 2] = np.round(hsv_values[..., 2] * 100 / 255).astype(np.int32)  # Konversi value ke 0-100
    
    # Ambil kombinasi unik HSV
    unique_hsv = np.unique(hsv_values.reshape(-1, 3), axis=0)
    
    # Hitung fitness berdasarkan kesesuaian dengan preferensi pengguna
    fitness = 0.0
    for pref in user_preferences:
        min_dist = float('inf')
        for hsv in unique_hsv:
            # Hitung jarak Euclidean dengan normalisasi komponen
            hue_diff = min(abs(hsv[0] - pref[0]), 360 - abs(hsv[0] - pref[0])) / 180.0
            sat_diff = abs(hsv[1] - pref[1]) / 100.0
            val_diff = abs(hsv[2] - pref[2]) / 100.0
            dist = np.sqrt(hue_diff**2 + sat_diff**2 + val_diff**2)
            if dist < min_dist:
                min_dist = dist
        fitness += (1.0 - min_dist)
    
    # Normalisasi fitness
    fitness = fitness / len(user_preferences)
    return fitness