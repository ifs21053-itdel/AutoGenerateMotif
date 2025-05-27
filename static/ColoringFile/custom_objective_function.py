import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    unique_colors = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert Hue to 0-360 range
    unique_colors[:, 0] = (unique_colors[:, 0].astype(np.int32) * 2) % 360
    
    # User preferences
    user_preferences = np.array([[353, 51, 28], [359, 91, 42], [50, 26, 100]])
    
    # Calculate fitness
    fitness = 0.0
    for color in unique_colors:
        for pref in user_preferences:
            # Calculate Euclidean distance in HSV space
            hue_diff = min(abs(color[0] - pref[0]), 360 - abs(color[0] - pref[0])) / 180.0
            sat_diff = abs(color[1] - pref[1]) / 255.0
            val_diff = abs(color[2] - pref[2]) / 255.0
            distance = np.sqrt(hue_diff**2 + sat_diff**2 + val_diff**2)
            similarity = 1.0 - distance
            fitness += max(0, similarity)  # Ensure non-negative
    
    # Normalize fitness by number of unique colors and preferences
    if len(unique_colors) > 0:
        fitness /= (len(unique_colors) * len(user_preferences))
    
    return fitness