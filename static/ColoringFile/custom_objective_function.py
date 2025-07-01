import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Predefined user preferences in HSV (H:0-360, S:0-255, V:0-255)
    user_preferences = np.array([
        [0, 0, 0],
        [18, 77, 57],
        [30, 20, 100],
        [0, 0, 100],
        [168, 60, 45]
    ], dtype=np.int32)
    
    # Extract unique HSV combinations from image
    hue_img = image_hsv[:, :, 0].astype(np.int32) * 2  # Convert to 0-360 range
    sat_img = image_hsv[:, :, 1].astype(np.int32)
    val_img = image_hsv[:, :, 2].astype(np.int32)
    
    # Stack and find unique combinations
    hsv_combinations = np.column_stack((hue_img.flatten(), sat_img.flatten(), val_img.flatten()))
    unique_hsv = np.unique(hsv_combinations, axis=0)
    
    # Calculate fitness based on color matching
    if len(unique_hsv) != len(user_preferences):
        fitness = 0.0
    else:
        matched = 0
        for pref in user_preferences:
            for hsv in unique_hsv:
                if np.allclose(hsv, pref, atol=5):  # Allow small tolerance
                    matched += 1
                    break
        fitness = matched / len(user_preferences)
    
    return fitness