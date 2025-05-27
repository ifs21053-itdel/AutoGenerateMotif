import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    hsv_combinations = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert hue to int32 and ensure it's within 0-360
    hsv_combinations[:, 0] = np.mod(hsv_combinations[:, 0].astype(np.int32), 360)
    hsv_combinations = hsv_combinations.astype(np.int32)
    
    # User preferences
    user_preferences = np.array([[359, 91, 42], [348, 74, 73], [30, 20, 100], [50, 26, 100], [50, 26, 100]], dtype=np.int32)
    
    # Calculate fitness based on matching combinations
    matching = 0
    for comb in hsv_combinations:
        if any(np.array_equal(comb, pref) for pref in user_preferences):
            matching += 1
    
    total_possible = len(user_preferences)
    fitness = matching / total_possible
    
    return fitness