"""
Racing Game UI Module

This module contains all UI-related classes and functions for the racing game.
It handles menus, in-game UI elements, and UI rendering.

Organization:
    1. UI Constants and Styles - Colors, sizes, and common styles
    2. UI Utility Functions - Helper functions for rendering UI elements
    3. Base UI Class - Foundation for all UI elements
    4. Menu UI Classes - Main menu, settings menu, pause menu
    5. In-Game UI Functions - HUD elements like speedometer and lap times
"""
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import os
import time
import json
from mapgen import load_map, generate_world
from video import Renderer


# --- CONFIG ---
WIDTH, HEIGHT = 1280, 720

# --- UTILS ---
def pygame_surface_to_opengl(surface, width, height, in_game):
    glPushAttrib(GL_ALL_ATTRIB_BITS)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, width, height, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    if in_game:  # Enable lighting only when in-game
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 10.0, 10.0, 1.0])  # Position the light
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])     # Diffuse light
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])    # Specular light
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
    try:
        if surface.get_bytesize() not in [3, 4]:  # Check for unsupported formats
            temp_path = os.path.join("temp_surface.png")
            pygame.image.save(surface, temp_path)  # Save as a compatible format
            surface = pygame.image.load(temp_path)  # Reload the converted surface
        data = pygame.image.tostring(surface, "RGBA", False)
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(),
                     0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(width, 0)
        glTexCoord2f(1, 1); glVertex2f(width, height)
        glTexCoord2f(0, 1); glVertex2f(0, height)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glDeleteTextures(1, [texture])
    finally:
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glPopAttrib()

def draw_button(surface, rect, label, font, hovered=False):
    color = (70, 170, 70) if hovered else (50, 150, 50)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, (255,255,255), rect, 2)
    text = font.render(label, True, (255,255,255))
    surface.blit(text, text.get_rect(center=rect.center))

def draw_text_centered(surface, text, font, y, color=(255,255,255)):
    text_surf = font.render(text, True, color)
    rect = text_surf.get_rect(center=(surface.get_width()//2, y))
    surface.blit(text_surf, rect)

def render_world(surface, world):
    """
    Render the generated world onto the surface.
    :param surface: Pygame surface to render on.
    :param world: World representation containing track, obstacles, etc.
    """
    # Example rendering logic for the track
    for segment in world["track"]:
        pygame.draw.lines(surface, (255, 255, 255), False, segment, 3)
    for checkpoint in world["checkpoints"]:
        pygame.draw.rect(surface, (0, 255, 0), checkpoint)
    for obstacle in world["obstacles"]:
        pygame.draw.circle(surface, (255, 0, 0), obstacle["position"], obstacle["radius"])

def load_track_parts(file_path="TrackParts.json"):
    """
    Load track parts definitions from a JSON file.
    :param file_path: Path to the JSON file containing track parts.
    :return: Dictionary of track parts.
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading track parts: {e}")
        return {}

def render_track(renderer, world, track_parts):
    """
    Render the track using the loaded track parts.
    :param renderer: Renderer instance for OpenGL rendering.
    :param world: World representation containing track layout.
    :param track_parts: Dictionary of track parts definitions.
    """
    for segment in world["track"]:
        part_type = segment.get("type", "straight")  # Default to "straight" if type is missing
        position = segment.get("position", [0, 0, 0])
        rotation = segment.get("rotation", [0, 0, 0])
        scale = segment.get("scale", [1, 1, 1])

        if part_type in track_parts:
            vertices = track_parts[part_type]["vertices"]
            faces = track_parts[part_type]["faces"]
            renderer.render_custom_mesh(vertices, faces, position, rotation, scale)
        else:
            print(f"Unknown track part type: {part_type}")

# --- MENUS ---
class LevelSelectionMenu:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.active = False
        self.levels = self._load_levels()
        self.selected_index = 0
        self.font = pygame.font.Font(None, 48)
        self.button_w, self.button_h = 400, 60
        self.button_pad = 20

    def _load_levels(self):
        levels_dir = "levels"
        levels = []
        if os.path.isdir(levels_dir):
            for fname in os.listdir(levels_dir):
                if fname.endswith(".json"):
                    levels.append({
                        "name": os.path.splitext(fname)[0].replace("_", " ").title(),
                        "path": os.path.join(levels_dir, fname)
                    })
        return levels or [{"name": "Demo Track", "path": "levels/demo.json"}]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.active = False
                return "back"
            elif event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
            elif event.key == pygame.K_DOWN:
                self.selected_index = min(len(self.levels) - 1, self.selected_index + 1)
            elif event.key == pygame.K_RETURN:
                return "select"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            for idx, rect in enumerate(self._level_rects()):
                if rect.collidepoint(mouse_pos):
                    self.selected_index = idx
                    return "select"
        return None

    def _level_rects(self):
        rects = []
        start_y = 180
        for i in range(len(self.levels)):
            rect = pygame.Rect(
                self.width//2 - self.button_w//2,
                start_y + i*(self.button_h+self.button_pad),
                self.button_w, self.button_h
            )
            rects.append(rect)
        return rects

    def render(self, surface):
        surface.fill((30,30,40))
        draw_text_centered(surface, "Select Level", self.font, 80)
        for idx, rect in enumerate(self._level_rects()):
            hovered = rect.collidepoint(pygame.mouse.get_pos()) or idx == self.selected_index
            draw_button(surface, rect, self.levels[idx]["name"], self.font, hovered)

class MainMenu:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.font = pygame.font.Font(None, 60)
        self.button_w, self.button_h = 350, 70
        self.buttons = {
            "start": pygame.Rect(width//2-175, 250, 350, 70),
            "select_level": pygame.Rect(width//2-175, 340, 350, 70),
            "settings": pygame.Rect(width//2-175, 430, 350, 70),
            "exit": pygame.Rect(width//2-175, 520, 350, 70)
        }
        self.level_selection_menu = LevelSelectionMenu(width, height)
        self.selected_level = None
        self.settings_active = False

    def handle_events(self, events):
        if self.level_selection_menu.active:
            for event in events:
                result = self.level_selection_menu.handle_event(event)
                if result == "back":
                    self.level_selection_menu.active = False
                elif result == "select":
                    self.selected_level = self.level_selection_menu.levels[self.level_selection_menu.selected_index]
                    self.level_selection_menu.active = False
                    return "start_game"
            return None
        if self.settings_active:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.settings_active = False
            return None
        for event in events:
            if event.type == pygame.QUIT:
                return "exit"
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "exit"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if self.buttons["start"].collidepoint(mouse_pos):
                    return "start_game"
                elif self.buttons["select_level"].collidepoint(mouse_pos):
                    self.level_selection_menu.active = True
                elif self.buttons["settings"].collidepoint(mouse_pos):
                    self.settings_active = True
                elif self.buttons["exit"].collidepoint(mouse_pos):
                    return "exit"
        return None

    def render(self, surface):
        surface.fill((20, 30, 60))
        draw_text_centered(surface, "Simple Racing Game", self.font, 120)
        for key, rect in self.buttons.items():
            label = {
                "start": "Quick Start",
                "select_level": "Select Level",
                "settings": "Settings",
                "exit": "Exit"
            }[key]
            hovered = rect.collidepoint(pygame.mouse.get_pos())
            draw_button(surface, rect, label, self.font, hovered)
        if self.level_selection_menu.active:
            self.level_selection_menu.render(surface)
        elif self.settings_active:
            surface.fill((40, 40, 60))
            draw_text_centered(surface, "Settings Menu", self.font, 120)
            draw_text_centered(surface, "Press ESC to return", self.font, 200)

def debug_info(game_state, selected_level, world, last_state):
    """
    Print debug information about the current game state only if it changes or an error occurs.
    :param game_state: Current state of the game (e.g., menu, in-game).
    :param selected_level: Currently selected level.
    :param world: Generated world data.
    :param last_state: Last recorded state for comparison.
    """
    if game_state != last_state["game_state"]:
        print(f"Game State Changed: {game_state}")
        last_state["game_state"] = game_state
    if selected_level != last_state["selected_level"]:
        if selected_level:
            print(f"Selected Level Changed: {selected_level['name']} (Path: {selected_level['path']})")
        else:
            print("Selected Level Changed: None")
        last_state["selected_level"] = selected_level
    if world != last_state["world"]:
        if world:
            print(f"World Info Updated: Track segments: {len(world['track'])}, Checkpoints: {len(world['checkpoints'])}, Obstacles: {len(world['obstacles'])}")
        else:
            print("World Info Updated: None")
        last_state["world"] = world

# --- MAIN LOOP ---
def main():
    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Simple Racing Game")
    renderer = Renderer(WIDTH, HEIGHT)  # Initialize the OpenGL renderer
    clock = pygame.time.Clock()
    ui_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    menu = MainMenu(WIDTH, HEIGHT)
    in_game = False
    selected_level = None
    world = None  # Placeholder for the generated world
    track_parts = load_track_parts()  # Load track parts definitions
    last_state = {"game_state": None, "selected_level": None, "world": None}  # Initialize last_state

    running = True
    while running:
        events = pygame.event.get()
        game_state = "menu" if not in_game else "in-game"
        debug_info(game_state, selected_level, world, last_state)  # Print debug info only on changes

        if not in_game:
            action = menu.handle_events(events)
            if action == "exit":
                running = False
            elif action == "start_game":
                selected_level = menu.selected_level or (menu.level_selection_menu.levels[0] if menu.level_selection_menu.levels else None)
                if selected_level:
                    try:
                        map_data = load_map(selected_level["path"])
                        world = generate_world(map_data)
                        in_game = True
                    except Exception as e:
                        print(f"Error loading level: {e}")
            # Force crash keybind (Ctrl+Shift+C)
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    raise Exception("Force crash triggered by user (Ctrl+Shift+C)")
            # Render menu
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            ui_surface.fill((0,0,0,0))
            menu.render(ui_surface)
            pygame_surface_to_opengl(ui_surface, WIDTH, HEIGHT, in_game)
            pygame.display.flip()
            clock.tick(60)
            continue

        # --- IN-GAME LOOP ---
        renderer.clear_screen()
        renderer.set_3d_mode()

        # Render the skybox
        camera_position = world.get("camera_position", [0, 0, 0])  # Default to origin if not provided
        renderer.render_skybox(camera_position)

        # Render the track using OpenGL
        if world:
            render_track(renderer, world, track_parts)

        # Render the car
        if world and "car" in world:
            car_data = world["car"]
            renderer.render_car(car_data["position"], car_data["rotation"], car_data["scale"])

        # Render grass or ground
        renderer.render_ground()

        renderer.set_2d_mode()
        ui_surface.fill((0, 0, 0, 0))
        pygame_surface_to_opengl(ui_surface, WIDTH, HEIGHT, in_game)
        renderer.update_display()

        for event in events:
            # Force crash keybind (Ctrl+Shift+C) in game
            if event.type == pygame.KEYDOWN and event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                raise Exception("Force crash triggered by user (Ctrl+Shift+C)")
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                in_game = False
        clock.tick(60)
    pygame.quit()

if __name__ == "__main__":
    main()