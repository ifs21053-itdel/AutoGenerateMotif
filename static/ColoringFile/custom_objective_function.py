import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Preferensi pengguna dalam HSV (H: 0-360, S: 0-100, V: 0-100)
    user_preferences = np.array([[30, 20, 100], [51, 100, 85]], dtype=np.float32)
    
    # Ekstrak kombinasi unik HSV dari gambar
    unique_colors = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Konversi ke format yang sesuai (H: 0-360, S: 0-100, V: 0-100)
    h = (unique_colors[:, 0].astype(np.int32) * 2).astype(np.float32)  # H: 0-359
    s = (unique_colors[:, 1].astype(np.float32) / 255 * 100)  # S: 0-100
    v = (unique_colors[:, 2].astype(np.float32) / 255 * 100)  # V: 0-100
    
    image_colors = np.column_stack((h, s, v))
    
    # Hitung perbedaan dengan preferensi pengguna
    min_distances = []
    for pref in user_preferences:
        # Hitung jarak Euclidean untuk setiap warna di gambar terhadap preferensi
        distances = np.sqrt(np.sum((image_colors - pref) ** 2, axis=1))
        min_distances.append(np.min(distances))
    
    # Hitung fitness berdasarkan jarak minimum
    avg_min_distance = np.mean(min_distances)
    fitness = 1.0 / (1.0 + avg_min_distance)
    
    return fitness