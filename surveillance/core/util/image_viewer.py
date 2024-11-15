#!/usr/bin/python3
# Run over ssh with DISPLAY=:0 in front of command
# For the example first cd to /home/opensurv/lib/ to make the logging setup work
# Example: cd /home/opensurv/lib/; DISPLAY=:0 core/util/image_viewer.py 100 100 500 400 10 20 https://images.opensurv.net/demo.png "test" 1

import pygame
import time
import sys
import io
import os
import urllib.request
from setuplogging import setup_logging

# Initialize Pygame
pygame.init()

# Get the screen dimensions
screen_info = pygame.display.Info()
screen_width, screen_height = screen_info.current_w, screen_info.current_h

# Check for command-line arguments
if len(sys.argv) != 10:
    print("Usage: script.py x1 y1 x2 y2 x_offset y_offset image_url_or_path window_title rotate90")
    print("Coordinates in omxplayer format: [x1, y1, x2, y2]")
    print("x_offset and y_offset: Offsets to adjust the window position")
    print("image_url_or_path: a URL starting with http(s):// or a local path with file://")
    print("window_title: Title for the window (visible in wmctrl -l)")
    print("rotate90: 0 for no rotation, 1 for 90-degree rotation")
    sys.exit(1)

# Parse command-line arguments
x1, y1, x2, y2 = map(int, sys.argv[1:5])
x_offset, y_offset = map(int, sys.argv[5:7])  #Offsets for another monitor
image_source = sys.argv[7]
window_title = sys.argv[8]
rotate90 = int(sys.argv[9])

logger = setup_logging(f"../logs/image_viewer_{window_title}.log", __name__)
logger.debug(f"image_viewer_{window_title} starting with arguments {x1}, {y1}, {x2}, {y2}, {x_offset}, {y_offset}, {image_source}, {window_title}, {rotate90}")

# Explanation of coordinates:
# x1: x-coordinate of the upper-left corner of the window
# y1: y-coordinate of the upper-left corner of the window
# x2: x-coordinate of the lower-right corner of the window (absolute position)
# y2: y-coordinate of the lower-right corner of the window (absolute position)

# Ensure coordinates are within screen boundaries
x1 = max(0, min(x1, screen_width))
y1 = max(0, min(y1, screen_height))
x2 = max(x1, min(x2, screen_width))
y2 = max(y1, min(y2, screen_height))

# Calculate window dimensions based on coordinates
window_width = x2 - x1  # Width from x1 to x2
window_height = y2 - y1  # Height from y1 to y2

# Set the window position using SDL environment variables, including offsets
os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x1 + x_offset},{y1 + y_offset}"

# Create a borderless window with specified dimensions
screen = pygame.display.set_mode((window_width, window_height), pygame.NOFRAME)
pygame.mouse.set_visible(False)

# Set the window title
pygame.display.set_caption(window_title)

def load_image():
    """Attempt to load the image and handle errors."""
    try:
        if image_source.startswith("http://") or image_source.startswith("https://"):
            # Load image from URL
            image_str = urllib.request.urlopen(image_source).read()
            image_file = io.BytesIO(image_str)
            img = pygame.image.load(image_file)
        elif image_source.startswith("file://"):
            # Load image from local file path
            local_path = image_source[7:]  # Remove the "file://" prefix
            img = pygame.image.load(local_path)
        else:
            logger.debug(f"image_viewer_{window_title} Error: Image source must start with 'http://', 'https://', or 'file://'")
            sys.exit(1)

        # Rotate the image if rotate90 is set to 1
        if rotate90 == 1:
            img = pygame.transform.rotate(img, -90)

        # Resize the image to fit the specified window dimensions
        return pygame.transform.scale(img, (window_width, window_height))
    except Exception as e:
        logger.debug(f"image_viewer_{window_title} Error loading image: {e}")
        return None

# Initial image load
image = load_image()
if image is None:
    logger.debug(f"image_viewer_{window_title} Failed to load the initial image. Exiting with error.")
    sys.exit(1)  # Exit with non-zero code if the initial image fails to load

last_refresh_time = time.time()
refresh_interval = 2  # Seconds to refresh the image

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Check if it's time to refresh the image
    if time.time() - last_refresh_time >= refresh_interval:
        logger.debug(f"image_viewer_{window_title}: Refreshing image with {image_source}")
        new_image = load_image()
        last_refresh_time = time.time()

        # If the new image fails to load, exit with an error
        if new_image is None:
            logger.debug(f"image_viewer_{window_title}: Failed to refresh the image. Exiting with error.")
            sys.exit(1)

        # Update the image to the new image
        image = new_image

    # Draw the image on the screen
    screen.blit(image, (0, 0))

    # Update the display
    pygame.display.flip()

    # Sleep for 1 second to reduce CPU usage
    time.sleep(1)

# Quit Pygame
pygame.quit()
