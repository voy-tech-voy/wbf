"""
Helper script to complete the size_estimator.py module extraction.
Appends remaining functions from conversion_engine.py.
"""

import os

# Read conversion_engine.py
with open(r'V:\_MY_APPS\ImgApp_1\client\core\conversion_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Extract the remaining functions we need (lines 1093-1826)
# These are: estimate_all_preset_sizes, find_optimal_gif_params_for_size,
# and all image/video estimation functions

# Lines to extract (0-indexed):
# 1092-1411: estimate_all_preset_sizes + find_optimal_gif_params_for_size  
# 1416-1826: image and video estimation functions

functions_to_add = []

# Add estimate_all_preset_sizes and find_optimal_gif_params_for_size
functions_to_add.extend(lines[1092:1411])

# Add image and video estimation functions  
functions_to_add.extend(lines[1416:1826])

# Append to size_estimator.py
with open(r'V:\_MY_APPS\ImgApp_1\client\core\size_estimator.py', 'a', encoding='utf-8') as f:
    f.write('\n')
    f.writelines(functions_to_add)

print(f'✓ Successfully appended {len(functions_to_add)} lines to size_estimator.py')
print('✓ Module extraction complete!')
