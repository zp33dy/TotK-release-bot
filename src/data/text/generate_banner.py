import os 
from typing import *

def interpolate_color(start_color, end_color, fraction):
    # Assuming start_color and end_color are tuples representing RGB values
    return tuple(int(start_color[i] + fraction * (end_color[i] - start_color[i])) for i in range(3))

def fade_blue_to_magenta(lines, num_lines) -> List[str]:
    start_color = (0, 0, 255)  # Blue
    end_color = (255, 0, 255)  # Magenta
    new_lines = []
    for i, line in enumerate(lines):
        fraction = i / (num_lines - 1)  # Calculate the interpolation factor
        interpolated_color = interpolate_color(start_color, end_color, fraction)
        # Apply the interpolated color to the line
        fmt = f"\033[38;2;{interpolated_color[0]};{interpolated_color[1]};{interpolated_color[2]}m{line}\033[0m"
        new_lines.append(fmt)
        
    return new_lines

# Example usage
# get pwd: os.getcwd()
with open(f"{os.getcwd()}/src/data/text/banner.txt") as file:
    lines = file.readlines()


new_lines = fade_blue_to_magenta(lines, len(lines))

# Print
for line in new_lines:
    print(line, end="")

# Save to file
with open(f"{os.getcwd()}/src/data/text/new_banner.txt", "w") as file:
    file.writelines(new_lines)
    
