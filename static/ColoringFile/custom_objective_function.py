import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    unique_colors = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert to correct data types and ranges
    hue_img = unique_colors[:, 0].astype(np.int32) * 2  # Convert to 0-360 range
    saturation_img = unique_colors[:, 1].astype(np.int32)
    value_img = unique_colors[:, 2].astype(np.int32)
    
    # User preferences (Hue in 0-360, Saturation and Value in 0-100)
    user_preferences = np.array([
        [351, 90, 73],
        [226, 30, 32],
        [0, 0, 100],
        [10, 80, 97],
        [335, 94, 69]
    ])
    
    # Normalize user preferences to match image ranges
    user_preferences_normalized = user_preferences.copy()
    user_preferences_normalized[:, 1] = (user_preferences[:, 1] * 255 / 100).astype(np.int32)
    user_preferences_normalized[:, 2] = (user_preferences[:, 2] * 255 / 100).astype(np.int32)
    
    # Calculate distances between each unique color and user preferences
    min_distances = []
    for color in zip(hue_img, saturation_img, value_img):
        h, s, v = color
        # Calculate Euclidean distance in HSV space
        distances = np.sqrt(
            (np.minimum(np.abs(h - user_preferences_normalized[:, 0]), 360 - np.abs(h - user_preferences_normalized[:, 0])) ** 2) +
            ((s - user_preferences_normalized[:, 1]) ** 2) +
            ((v - user_preferences_normalized[:, 2]) ** 2)
        )
        min_distances.append(np.min(distances))
    
    if not min_distances:
        return 0.0
    
    # Normalize fitness based on distances (lower distance = higher fitness)
    max_possible_distance = np.sqrt(360**2 + 255**2 + 255**2)
    normalized_fitness = 1.0 - (np.mean(min_distances) / max_possible_distance)
    
    return max(0.0, normalized_fitness)