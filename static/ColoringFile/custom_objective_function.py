import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    hsv_combinations = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert hue to 0-360 range
    hsv_combinations_360 = hsv_combinations.copy()
    hsv_combinations_360[:, 0] = (hsv_combinations[:, 0].astype(np.int32) * 2) % 360
    
    # User preferences
    user_preferences = np.array([[0, 0, 0], [51, 100, 85]])
    
    # Calculate fitness
    min_distances = []
    for pref in user_preferences:
        distances = np.sqrt(np.sum((hsv_combinations_360 - pref)**2, axis=1))
        min_distances.append(np.min(distances))
    
    max_possible_distance = np.sqrt(360**2 + 255**2 + 255**2)
    fitness = 1 - np.mean(min_distances) / max_possible_distance
    
    return fitness