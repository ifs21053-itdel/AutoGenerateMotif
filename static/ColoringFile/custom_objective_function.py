import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    hsv_combinations = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert hue to 0-360 range
    hue = hsv_combinations[:, 0].astype(np.int32) * 2
    saturation = hsv_combinations[:, 1]
    value = hsv_combinations[:, 2]
    
    # User preferences
    user_preferences = np.array([[0, 0, 0], [18, 75, 44]])
    
    # Calculate fitness
    min_distance = float('inf')
    for pref in user_preferences:
        for h, s, v in zip(hue, saturation, value):
            # Calculate Euclidean distance in HSV space
            dh = min(abs(h - pref[0]), 360 - abs(h - pref[0])) / 360.0
            ds = abs(s - pref[1]) / 255.0
            dv = abs(v - pref[2]) / 255.0
            distance = np.sqrt(dh**2 + ds**2 + dv**2)
            if distance < min_distance:
                min_distance = distance
    
    # Normalize fitness (1 - distance)
    fitness = 1.0 - min_distance
    return fitness