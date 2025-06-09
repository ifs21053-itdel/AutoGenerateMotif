import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    unique_colors = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert hue to 0-360 range
    hue = unique_colors[:, 0].astype(np.int32) * 2
    sat = unique_colors[:, 1]
    val = unique_colors[:, 2]
    
    user_preferences = np.array([[353, 51, 28], [331, 97, 92]])
    
    # Calculate color differences
    min_distances = []
    for color in unique_colors:
        h, s, v = color[0] * 2, color[1], color[2]
        distances = np.sqrt(
            (np.minimum(np.abs(h - user_preferences[:, 0]), 360 - np.abs(h - user_preferences[:, 0])) / 180.0) ** 2 +
            ((s - user_preferences[:, 1]) / 255.0) ** 2 +
            ((v - user_preferences[:, 2]) / 255.0) ** 2
        )
        min_dist = np.min(distances)
        min_distances.append(min_dist)
    
    if not min_distances:
        return 0.0
    
    avg_distance = np.mean(min_distances)
    fitness = 1.0 / (1.0 + avg_distance)
    
    return fitness