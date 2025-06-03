import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Predefined user preferences in HSV (H: 0-360, S: 0-100, V: 0-100)
    user_preferences = [
        [351, 90, 73], [360, 47, 69], [0, 0, 100], [30, 20, 100], 
        [331, 97, 92], [51, 100, 85], [335, 94, 69], [50, 26, 100], 
        [268, 57, 61], [113, 48, 53], [0, 0, 0], [18, 77, 57], 
        [168, 60, 45], [205, 60, 100], [225, 61, 70], [226, 30, 32], 
        [248, 68, 54], [348, 74, 73], [0, 63, 77]
    ]
    
    # Convert image HSV to match user preference format
    hue_img = image_hsv[:, :, 0].astype(np.int32) * 2  # Convert OpenCV Hue (0-179) to 0-358
    sat_img = (image_hsv[:, :, 1] / 255 * 100).astype(np.int32)  # Convert Saturation to 0-100
    val_img = (image_hsv[:, :, 2] / 255 * 100).astype(np.int32)  # Convert Value to 0-100
    
    # Get all unique HSV combinations in the image
    hsv_combinations = np.column_stack((hue_img.flatten(), sat_img.flatten(), val_img.flatten()))
    unique_hsv = np.unique(hsv_combinations, axis=0)
    
    # Convert user preferences to numpy array for comparison
    user_pref_array = np.array(user_preferences)
    
    # Calculate fitness based on matching HSV combinations
    matching_count = 0
    for hsv in unique_hsv:
        for pref in user_pref_array:
            if np.allclose(hsv, pref, atol=5):  # Allow small tolerance for Hue, Saturation, Value
                matching_count += 1
                break
    
    total_user_prefs = len(user_preferences)
    fitness = matching_count / total_user_prefs
    
    return fitness