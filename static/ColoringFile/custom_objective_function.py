import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    unique_colors = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert to proper ranges (H: 0-360, S: 0-100, V: 0-100)
    converted_colors = []
    for color in unique_colors:
        h, s, v = color
        # Convert hue to 0-360
        h_converted = int(h) * 2  # Since OpenCV uses 0-179 for hue
        # Convert saturation and value to 0-100
        s_converted = int(s) * 100 / 255
        v_converted = int(v) * 100 / 255
        converted_colors.append([h_converted, s_converted, v_converted])
    
    # User preferences
    user_preferences = [[0, 0, 0], [353, 51, 28], [359, 91, 42], [0, 0, 100]]
    
    # Calculate fitness
    if len(converted_colors) != len(user_preferences):
        fitness = 0.0
    else:
        total_diff = 0.0
        for uc, up in zip(sorted(converted_colors), sorted(user_preferences)):
            h_diff = min(abs(uc[0] - up[0]), 360 - abs(uc[0] - up[0])) / 360.0
            s_diff = abs(uc[1] - up[1]) / 100.0
            v_diff = abs(uc[2] - up[2]) / 100.0
            total_diff += h_diff + s_diff + v_diff
        max_diff = len(user_preferences) * 3  # Maximum possible difference
        fitness = 1.0 - (total_diff / max_diff)
    
    return max(0.0, fitness)  # Ensure fitness is not negative