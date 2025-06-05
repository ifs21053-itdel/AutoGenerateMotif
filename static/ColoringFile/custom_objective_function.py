import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    hsv_combinations = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert Hue to 0-360 range and ensure int32
    hsv_combinations[:, 0] = (hsv_combinations[:, 0].astype(np.int32) * 2) % 360
    hsv_combinations[:, 1] = hsv_combinations[:, 1].astype(np.int32)
    hsv_combinations[:, 2] = hsv_combinations[:, 2].astype(np.int32)
    
    # User preferences
    user_preferences = np.array([[359, 91, 42], [0, 0, 100]], dtype=np.int32)
    
    # Calculate fitness
    min_distance = float('inf')
    for user_hsv in user_preferences:
        for img_hsv in hsv_combinations:
            # Calculate Euclidean distance in HSV space
            hue_diff = min(abs(user_hsv[0] - img_hsv[0]), 360 - abs(user_hsv[0] - img_hsv[0])) / 360.0
            sat_diff = abs(user_hsv[1] - img_hsv[1]) / 255.0
            val_diff = abs(user_hsv[2] - img_hsv[2]) / 255.0
            distance = np.sqrt(hue_diff**2 + sat_diff**2 + val_diff**2)
            
            if distance < min_distance:
                min_distance = distance
    
    # Normalize fitness (1 - distance)
    fitness = 1.0 - min_distance
    return fitness