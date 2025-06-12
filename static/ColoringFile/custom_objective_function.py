import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Preferensi pengguna dalam HSV (H: 0-360, S: 0-100, V: 0-100)
    user_preferences = np.array([[30, 20, 100], [51, 100, 85]], dtype=np.float32)
    
    # Convert hue to 0-360 range
    hsv_combinations_360 = hsv_combinations.copy()
    hsv_combinations_360[:, 0] = (hsv_combinations[:, 0].astype(np.int32) * 2) % 360
    
    # Konversi ke format yang sesuai (H: 0-360, S: 0-100, V: 0-100)
    h = (unique_colors[:, 0].astype(np.int32) * 2).astype(np.float32)  # H: 0-359
    s = (unique_colors[:, 1].astype(np.float32) / 255 * 100)  # S: 0-100
    v = (unique_colors[:, 2].astype(np.float32) / 255 * 100)  # V: 0-100
    
    # Calculate fitness
    min_distances = []
    for pref in user_preferences:
        distances = np.sqrt(np.sum((hsv_combinations_360 - pref)**2, axis=1))
        min_distances.append(np.min(distances))
    
    max_possible_distance = np.sqrt(360**2 + 255**2 + 255**2)
    fitness = 1 - np.mean(min_distances) / max_possible_distance
    
    return fitness