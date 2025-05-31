import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    hsv_combinations = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert hue to 0-360 range
    hsv_combinations = hsv_combinations.astype(np.int32)
    hsv_combinations[:, 0] = (hsv_combinations[:, 0] * 2) % 360
    
    # User preferences (Hue: 0-360, Saturation: 0-255, Value: 0-255)
    user_preferences = np.array([
        [30, 20, 100],
        [0, 0, 100],
        [0, 0, 0]
    ], dtype=np.int32)
    
    # Calculate fitness
    min_distance = float('inf')
    for user_hsv in user_preferences:
        for img_hsv in hsv_combinations:
            # Calculate Euclidean distance in HSV space
            hue_diff = min(abs(user_hsv[0] - img_hsv[0]), 360 - abs(user_hsv[0] - img_hsv[0]))
            sat_diff = abs(user_hsv[1] - img_hsv[1])
            val_diff = abs(user_hsv[2] - img_hsv[2])
            
            distance = np.sqrt(hue_diff**2 + sat_diff**2 + val_diff**2)
            if distance < min_distance:
                min_distance = distance
    
    # Normalize distance to fitness value (lower distance = higher fitness)
    max_possible_distance = np.sqrt(360**2 + 255**2 + 255**2)
    fitness = 1 - (min_distance / max_possible_distance)
    
    return fitness
