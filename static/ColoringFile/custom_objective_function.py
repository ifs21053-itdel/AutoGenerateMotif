import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    unique_colors = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert Hue to 0-360 range
    hue = unique_colors[:, 0].astype(np.int32) * 2
    saturation = unique_colors[:, 1].astype(np.int32)
    value = unique_colors[:, 2].astype(np.int32)
    
    # User preferences
    user_preferences = np.array([[359, 91, 42], [353, 51, 28]])
    
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
    
    # Normalize fitness (closer distance -> higher fitness)
    fitness = 1.0 - min_distance
    return fitness