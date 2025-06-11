import numpy as np

def calculate_user_color_preferences(image_hsv):
    # Extract unique HSV combinations
    hsv_combinations = np.unique(image_hsv.reshape(-1, 3), axis=0)
    
    # Convert hue to 0-360 range
    hue_converted = (hsv_combinations[:, 0].astype(np.int32) * 2) % 360
    hsv_combinations_converted = np.column_stack((
        hue_converted,
        hsv_combinations[:, 1],
        hsv_combinations[:, 2]
    ))
    
    # User preferences
    user_preferences = np.array([[0, 0, 0], [51, 100, 85]])
    
    # Calculate fitness
    min_distance = float('inf')
    for user_color in user_preferences:
        for img_color in hsv_combinations_converted:
            # Calculate Euclidean distance in HSV space
            distance = np.sqrt(
                ((user_color[0] - img_color[0]) / 360.0)**2 +
                ((user_color[1] - img_color[1]) / 255.0)**2 +
                ((user_color[2] - img_color[2]) / 255.0)**2
            )
            if distance < min_distance:
                min_distance = distance
    
    # Normalize fitness (1 - normalized distance)
    max_possible_distance = np.sqrt(3)  # sqrt(1 + 1 + 1)
    fitness = 1 - (min_distance / max_possible_distance)
    
    return fitness