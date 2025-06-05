import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    unique_colors = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert Hue to 0-360 range
    hue = unique_colors[:, 0].astype(np.int32) * 2  # Convert to 0-360
    sat = unique_colors[:, 1]
    val = unique_colors[:, 2]
    
    # User preferences
    user_preferences = np.array([[0, 0, 0], [0, 0, 100]])
    
    # Calculate fitness
    min_distance = float('inf')
    for color in unique_colors:
        h, s, v = color
        h = int(h) * 2  # Convert to 0-360
        for pref in user_preferences:
            hp, sp, vp = pref
            # Calculate Euclidean distance in HSV space
            distance = np.sqrt((h - hp)**2 + (s - sp)**2 + (v - vp)**2)
            if distance < min_distance:
                min_distance = distance
    
    # Normalize fitness (lower distance is better)
    max_possible_distance = np.sqrt(360**2 + 255**2 + 255**2)
    fitness = 1.0 - (min_distance / max_possible_distance)
    
    return fitness