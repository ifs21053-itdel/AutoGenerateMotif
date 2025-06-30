import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Predefined user preferences in HSV (H:0-360, S:0-100, V:0-100)
    user_preferences = np.array([
        [18, 77, 57],
        [1, 88, 80],
        [30, 20, 100],
        [205, 60, 100],
        [0, 0, 100]
    ], dtype=np.int32)
    
    # Extract unique HSV combinations from image
    hsv_combinations = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert image HSV to match user preference format
    # Hue: 0-179 -> 0-360 (scale by 2)
    # Saturation: 0-255 -> 0-100 (scale by 100/255)
    # Value: 0-255 -> 0-100 (scale by 100/255)
    h_img = (hsv_combinations[:, 0].astype(np.int32) * 2) % 360
    s_img = (hsv_combinations[:, 1] * 100 / 255).astype(np.int32)
    v_img = (hsv_combinations[:, 2] * 100 / 255).astype(np.int32)
    
    image_hsv_converted = np.column_stack((h_img, s_img, v_img))
    
    # Calculate fitness based on matching colors
    match_count = 0
    for pref in user_preferences:
        for img_color in image_hsv_converted:
            if np.array_equal(pref, img_color):
                match_count += 1
                break
    
    # Calculate fitness score (normalized to 0-1)
    fitness = match_count / len(user_preferences)
    
    return fitness