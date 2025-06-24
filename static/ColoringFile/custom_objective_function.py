import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Preferensi pengguna dalam format HSV
    user_preferences = np.array([[0, 0, 88], [268, 57, 61], [0, 77, 86]], dtype=np.int32)
    
    # Ekstrak kombinasi unik HSV dari gambar
    unique_colors = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Konversi hue ke rentang 0-360
    hue_converted = unique_colors[:, 0].astype(np.int32) * 2  # Karena OpenCV hue range 0-179
    
    # Gabungkan kembali dengan S dan V
    unique_colors_converted = np.column_stack((hue_converted, unique_colors[:, 1], unique_colors[:, 2])).astype(np.int32)
    
    # Hitung jumlah warna yang sesuai dengan preferensi pengguna
    matched = 0
    for pref in user_preferences:
        for color in unique_colors_converted:
            if np.allclose(color, pref, atol=10):  # Tolerance untuk perbedaan kecil
                matched += 1
                break
    
    # Hitung fitness berdasarkan rasio warna yang sesuai
    fitness = matched / len(user_preferences)
    
    return fitness