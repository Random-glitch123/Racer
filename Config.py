import pygame

"""
Confing File

Do not mess with this or you could break something (or everything)
This file is used to configure the car physics and player controls in a racing game.

"""

# Car configuration
CAR_POSITION = [0, 5, 0]  # Initial car position
CAR_SPEED = 0.2  # Default car speed
CAR_DRIFT_FACTOR = 0.7  # Drift multiplier for turning radius
CAR_DRIFT_SPEED_THRESHOLD = 70 / 3.6  # Speed threshold for drifting in m/s

# Acceleration and braking rates
CAR_ACCELERATION = 0.02  # Rate of acceleration
CAR_BRAKING = 0.03  # Rate of braking
CAR_MAX_SPEED = 250 / 3.6  # Max speed in m/s (converted from km/h)

# Keybinds
KEYBINDS = {
    "move_forward": [pygame.K_UP, pygame.K_w],
    "move_backward": [pygame.K_DOWN, pygame.K_s],
    "turn_left": [pygame.K_LEFT, pygame.K_a],
    "turn_right": [pygame.K_RIGHT, pygame.K_d],
    "change_camera": pygame.K_c
}

