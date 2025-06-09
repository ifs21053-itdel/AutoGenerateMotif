import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    hsv_combinations = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert Hue to 0-360 range
    hue_converted = (hsv_combinations[:, 0].astype(np.int32) * 2) % 360
    hsv_combinations[:, 0] = hue_converted
    
    # User preferences
    user_preferences = np.array([[348, 74, 73], [0, 0, 100]])
    
    # Calculate fitness
    min_distance = float('inf')
    for user_hsv in user_preferences:
        for img_hsv in hsv_combinations:
            # Calculate Euclidean distance in HSV space
            distance = np.sqrt(np.sum((user_hsv - img_hsv) ** 2))
            if distance < min_distance:
                min_distance = distance
    
    # Normalize fitness (lower distance = higher fitness)
    max_possible_distance = np.sqrt(360**2 + 255**2 + 255**2)
    fitness = 1 - (min_distance / max_possible_distance)
    
    return fitness