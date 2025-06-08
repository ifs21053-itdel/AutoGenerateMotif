import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    unique_colors = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert hue to 0-360 range and ensure int32
    hue_converted = (unique_colors[:, 0].astype(np.int32) * 2) % 360
    unique_colors_converted = np.column_stack((
        hue_converted,
        unique_colors[:, 1].astype(np.int32),
        unique_colors[:, 2].astype(np.int32)
    ))
    
    # User preferences
    user_preferences = np.array([
        [0, 0, 0],
        [10, 80, 97],
        [113, 48, 53]
    ], dtype=np.int32)
    
    # Calculate fitness
    if len(unique_colors_converted) != len(user_preferences):
        fitness = 0.0
    else:
        # Calculate color differences
        diff = np.abs(unique_colors_converted - user_preferences)
        hue_diff = np.minimum(diff[:, 0], 360 - diff[:, 0])  # Circular difference for hue
        sat_diff = diff[:, 1]
        val_diff = diff[:, 2]
        
        # Normalize differences
        hue_diff_norm = hue_diff / 180.0  # Max hue difference is 180
        sat_diff_norm = sat_diff / 255.0
        val_diff_norm = val_diff / 255.0
        
        # Weighted sum of differences
        total_diff = np.mean(hue_diff_norm + sat_diff_norm + val_diff_norm)
        fitness = 1.0 - total_diff
    
    return max(fitness, 0.0)  # Ensure fitness is non-negative