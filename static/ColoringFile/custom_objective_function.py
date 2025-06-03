import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    unique_colors = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert Hue to 0-360 range
    hue = unique_colors[:, 0].astype(np.int32) * 2  # Convert from 0-179 to 0-358
    saturation = unique_colors[:, 1].astype(np.int32)
    value = unique_colors[:, 2].astype(np.int32)
    
    # Combine into HSV array in 0-360, 0-255, 0-255 range
    extracted_colors = np.column_stack((hue, saturation, value))
    
    # User preferences
    user_preferences = np.array([[359, 91, 42], [360, 47, 69], [30, 20, 100]])
    
    # Calculate fitness
    min_distances = []
    for pref in user_preferences:
        distances = np.sqrt(np.sum((extracted_colors - pref) ** 2, axis=1))
        min_distances.append(np.min(distances))
    
    avg_distance = np.mean(min_distances)
    max_possible_distance = np.sqrt(360**2 + 255**2 + 255**2)
    fitness = 1 - (avg_distance / max_possible_distance)
    
    return max(fitness, 0)