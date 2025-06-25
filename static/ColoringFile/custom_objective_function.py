import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    unique_colors = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert Hue to 0-360 range
    hue = unique_colors[:, 0].astype(np.int32) * 2  # Scale 0-179 to 0-358
    saturation = unique_colors[:, 1]
    value = unique_colors[:, 2]
    
    # User preferences (Hue: 0-360, Saturation: 0-255, Value: 0-255)
    user_preferences = np.array([
        [18, 75, 44],
        [200, 35, 100],
        [0, 0, 88]
    ])
    
    # Calculate fitness based on color distance
    min_distances = []
    for pref in user_preferences:
        # Calculate Euclidean distance in HSV space
        hue_diff = np.minimum(np.abs(hue - pref[0]), 360 - np.abs(hue - pref[0])) / 180.0
        sat_diff = np.abs(saturation - pref[1]) / 255.0
        val_diff = np.abs(value - pref[2]) / 255.0
        
        distances = np.sqrt(hue_diff**2 + sat_diff**2 + val_diff**2)
        min_distances.append(np.min(distances))
    
    avg_min_distance = np.mean(min_distances)
    fitness = 1.0 / (1.0 + avg_min_distance)
    
    return fitness