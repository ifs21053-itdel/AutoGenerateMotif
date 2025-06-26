import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Predefined user preferences in HSV (H: 0-360, S: 0-100, V: 0-100)
    user_preferences = np.array([[69, 73, 79], [348, 74, 73]], dtype=np.int32)
    
    # Convert image HSV to match user preference format
    hue_img = image_hsv[:, :, 0].astype(np.int32) * 2  # Convert H from 0-179 to 0-358
    sat_img = (image_hsv[:, :, 1].astype(np.float32) / 255 * 100).astype(np.int32)  # Convert S from 0-255 to 0-100
    val_img = (image_hsv[:, :, 2].astype(np.float32) / 255 * 100).astype(np.int32)  # Convert V from 0-255 to 0-100
    
    # Get all unique HSV combinations in the image
    hsv_combinations = np.unique(np.column_stack((hue_img.flatten(), sat_img.flatten(), val_img.flatten())), axis=0)
    
    # Calculate fitness based on how close the image colors match user preferences
    fitness = 0.0
    for pref in user_preferences:
        min_dist = float('inf')
        for img_color in hsv_combinations:
            # Calculate Euclidean distance in HSV space
            h_diff = min(abs(pref[0] - img_color[0]), 360 - abs(pref[0] - img_color[0])) / 180.0
            s_diff = abs(pref[1] - img_color[1]) / 100.0
            v_diff = abs(pref[2] - img_color[2]) / 100.0
            dist = np.sqrt(h_diff**2 + s_diff**2 + v_diff**2)
            if dist < min_dist:
                min_dist = dist
        fitness += (1.0 - min_dist)
    
    # Normalize fitness to range [0, 1]
    fitness /= len(user_preferences)
    return fitness