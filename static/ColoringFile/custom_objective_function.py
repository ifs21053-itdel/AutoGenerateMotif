import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Predefined user preferences in HSV (H: 0-360, S: 0-100, V: 0-100)
    user_preferences = np.array([[0, 0, 0], [1, 88, 80]], dtype=np.float32)
    
    # Convert image HSV to match user preference format
    hue_img = image_hsv[:, :, 0].astype(np.int32) * 2  # Convert H to 0-360
    sat_img = (image_hsv[:, :, 1].astype(np.float32) / 255) * 100  # Convert S to 0-100
    val_img = (image_hsv[:, :, 2].astype(np.float32) / 255) * 100  # Convert V to 0-100
    
    # Get unique HSV combinations
    hsv_combinations = np.column_stack((hue_img.flatten(), sat_img.flatten(), val_img.flatten()))
    unique_combinations = np.unique(hsv_combinations, axis=0)
    
    # Calculate fitness based on similarity to user preferences
    fitness = 0.0
    for combo in unique_combinations:
        min_dist = float('inf')
        for pref in user_preferences:
            # Calculate distance in HSV space (weighted components)
            h_diff = min(abs(combo[0] - pref[0]), 360 - abs(combo[0] - pref[0])) / 360.0
            s_diff = abs(combo[1] - pref[1]) / 100.0
            v_diff = abs(combo[2] - pref[2]) / 100.0
            dist = np.sqrt(0.5 * h_diff**2 + 0.3 * s_diff**2 + 0.2 * v_diff**2)
            if dist < min_dist:
                min_dist = dist
        fitness += (1.0 - min_dist)
    
    # Normalize fitness by number of unique combinations
    if len(unique_combinations) > 0:
        fitness /= len(unique_combinations)
    
    return fitness