import numpy as np

def calculate_user_color_preferences(hsv_image):
    # Predefined user preferences in HSV [Hue (0-360), Saturation (0-100), Value (0-100)]
    user_preferences = np.array([
        [268, 57, 61],
        [50, 26, 100],
        [140, 100, 60]
    ], dtype=np.int32)
    
    # Convert image to HSV and get unique colors
    hsv_image = hsv_image.astype(np.int32)
    hue_img = hsv_image[..., 0] * 2  # Convert OpenCV Hue range (0-179) to (0-358)
    sat_img = (hsv_image[..., 1] * 100) // 255  # Convert Saturation to (0-100)
    val_img = (hsv_image[..., 2] * 100) // 255  # Convert Value to (0-100)
    
    # Stack and get unique HSV combinations
    hsv_combinations = np.column_stack((hue_img.flatten(), sat_img.flatten(), val_img.flatten()))
    unique_hsv = np.unique(hsv_combinations, axis=0)
    
    # Calculate fitness based on color matching
    fitness = 0.0
    for pref in user_preferences:
        for color in unique_hsv:
            # Calculate Euclidean distance in HSV space
            hue_diff = min(abs(color[0] - pref[0]), 360 - abs(color[0] - pref[0])) / 360.0
            sat_diff = abs(color[1] - pref[1]) / 100.0
            val_diff = abs(color[2] - pref[2]) / 100.0
            distance = np.sqrt(hue_diff**2 + sat_diff**2 + val_diff**2)
            
            # Contribution to fitness is inversely proportional to distance
            if distance == 0:
                fitness += 1.0
            else:
                fitness += 1.0 / (1.0 + distance)
    
    # Normalize fitness by the number of user preferences
    fitness /= len(user_preferences)
    return fitness