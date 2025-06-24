import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Preferensi pengguna dalam format HSV
    user_preferences = np.array([[0, 0, 88], [268, 57, 61], [0, 77, 86]], dtype=np.int32)
    
    # Ekstrak kombinasi unik HSV dari gambar
    unique_colors = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert hue to 0-360 range
    hue_converted = (unique_colors[:, 0].astype(np.int32) * 2) % 360
    unique_colors[:, 0] = hue_converted
    
    # User preferences
    user_preferences = np.array([[0, 0, 0], [335, 94, 69]])
    
    # Hitung jumlah warna yang sesuai dengan preferensi pengguna
    matched = 0
    for pref in user_preferences:
        distances = np.sqrt(np.sum((unique_colors - pref) ** 2, axis=1))
        current_min = np.min(distances)
        if current_min < min_distance:
            min_distance = current_min
    
    # Normalize fitness (lower distance is better)
    max_possible_distance = np.sqrt(360**2 + 255**2 + 255**2)
    fitness = 1 - (min_distance / max_possible_distance)
    
    return fitness