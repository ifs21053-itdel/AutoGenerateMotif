import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    unique_colors = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert Hue to 0-360 range
    hue_converted = (unique_colors[:, 0].astype(np.int32) * 2) % 360
    unique_colors[:, 0] = hue_converted
    
    # User preferences (Hue in 0-360 range, Saturation and Value in 0-100 range)
    user_prefs = np.array([
        [18, 75, 44],
        [56, 100, 100]
    ])
    
    # Normalize Saturation and Value to 0-255 range for comparison
    user_prefs[:, 1] = (user_prefs[:, 1] / 100) * 255
    user_prefs[:, 2] = (user_prefs[:, 2] / 100) * 255
    
    # Calculate color distances
    min_distances = []
    for user_color in user_prefs:
        distances = np.sqrt(np.sum((unique_colors - user_color) ** 2, axis=1))
        min_distances.append(np.min(distances))
    
    # Normalize distances to fitness value (0-1)
    max_possible_distance = np.sqrt(360**2 + 255**2 + 255**2)
    fitness = 1 - (np.mean(min_distances) / max_possible_distance)
    
    return max(0, fitness)  # Ensure fitness is not negative