"""

Racing Game Module

This module contains the main classes and functions for the racing game,
integrating rendering and physics calculations.
"""

# --- Imports ---
import pyaudio
import pygame
import moderngl
import struct
import time
import math
import os
from pyrr import Matrix44
import moderngl_window
from moderngl_window import geometry
from moderngl_window.resources import register_dir
from pathlib import Path

# --- Constants ---
WIDTH, HEIGHT = 1280, 720
DEBUG_MODE = False  # Set to False to disable debugging
FORCE_CRASH_MSG = "Force crash triggered by Ctrl+Shift+C"

# --- Utility Functions ---
def debug_log(message):
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")
        time.sleep(2)

# --- Renderer Section ---
class Renderer:
    def __init__(self, ctx, width, height):
        self.ctx = ctx
        self.width = width
        self.height = height
        self.prog = self.ctx.program(
            vertex_shader="""
            #version 330
            in vec2 in_vert;
            void main() {
                gl_Position = vec4(in_vert, 0.0, 1.0);
            }
            """,
            fragment_shader="""
            #version 330
            out vec4 fragColor;
            void main() {
                fragColor = vec4(1.0, 0.0, 0.0, 1.0);
            }
            """
        )
        self.vbo = self.ctx.buffer(
            struct.pack(
                '8f',
                -1.0, -1.0,
                 1.0, -1.0,
                -1.0,  1.0,
                 1.0,  1.0
            )
        )
        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, 'in_vert')

    def render(self):
        self.vao.render(moderngl.TRIANGLE_STRIP)

# --- Button Section ---
class Button:
    def __init__(self, text, pos, size, font, base_color, hover_color):
        self.text = text
        self.pos = list(pos)  # Fixed position, never changes
        self.size = list(size)
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.is_hovered = False
        self.base_alpha = 128
        self.hover_alpha = 255
        self.current_alpha = self.base_alpha
        self.growth = 1.08  # 8% larger on hover
        self.animation_speed = 0.22
        self.current_size = list(size)
        self.target_size = list(size)
        self.target_alpha = self.base_alpha

    def update(self, mouse_pos):
        rect = pygame.Rect(self.pos, self.size)
        self.is_hovered = rect.collidepoint(mouse_pos)
        if self.is_hovered:
            self.target_size = [int(self.size[0]*self.growth), int(self.size[1]*self.growth)]
            self.target_alpha = self.hover_alpha
        else:
            self.target_size = list(self.size)
            self.target_alpha = self.base_alpha
        # Animate size (centered on original position)
        for i in (0,1):
            self.current_size[i] += int((self.target_size[i] - self.current_size[i]) * self.animation_speed)
        self.current_alpha += int((self.target_alpha - self.current_alpha) * self.animation_speed)

    def draw(self, surface):
        # Draw the button centered at the original position
        offset_x = (self.current_size[0] - self.size[0]) // 2
        offset_y = (self.current_size[1] - self.size[1]) // 2
        draw_pos = [self.pos[0] - offset_x, self.pos[1] - offset_y]
        btn_surf = pygame.Surface(self.current_size, pygame.SRCALPHA)
        color = self.hover_color if self.is_hovered else self.base_color
        btn_surf.fill((*color, self.current_alpha))
        text_surf = self.font.render(self.text, True, (0,0,0))
        text_rect = text_surf.get_rect(center=(self.current_size[0]//2, self.current_size[1]//2))
        btn_surf.blit(text_surf, text_rect)
        surface.blit(btn_surf, draw_pos)

    def is_clicked(self, mouse_pos, mouse_pressed):
        rect = pygame.Rect(self.pos, self.size)
        return rect.collidepoint(mouse_pos) and mouse_pressed[0]

# --- Main Menu Section ---
class MainMenu:
    def __init__(self, ctx):
        self.ctx = ctx
        self.ctx.enable(moderngl.BLEND)
        self.background_texture = self.load_texture("assets/textures/BackgroundImage.jpeg")
        left_x = 60
        button_width = 200
        button_height = 50
        button_spacing = 20
        button_names = ["Start", "Multiplayer", "Options", "Credits", "Exit Game"]
        bottom_y = 60
        self.font = pygame.font.Font(None, 36)
        self.buttons = []
        for idx, name in enumerate(button_names):
            y = bottom_y + (button_height + button_spacing) * idx
            btn = Button(
                text=name,
                pos=[left_x, y],
                size=[button_width, button_height],
                font=self.font,
                base_color=(0, 0, 255),
                hover_color=(255, 0, 0)
            )
            self.buttons.append(btn)

    def load_texture(self, path):
        surface = pygame.image.load(path)
        # Flip vertically for OpenGL bottom-left origin
        surface = pygame.transform.flip(surface, False, True)
        data = pygame.image.tostring(surface, "RGBA", False)
        texture = self.ctx.texture((surface.get_width(), surface.get_height()), 4, data)
        texture.build_mipmaps()
        return texture

    def render(self):
        # Render the background
        self.ctx.clear(0.1, 0.1, 0.1, 1.0)
        self.background_texture.use(location=0)
        quad = self.ctx.buffer(
            struct.pack(
                '8f',
                -1.0, -1.0,
                 1.0, -1.0,
                -1.0,  1.0,
                 1.0,  1.0
            )
        )
        bg_prog = self.ctx.program(
            vertex_shader="""
            #version 330
            in vec2 in_vert;
            out vec2 tex_coord;
            void main() {
                tex_coord = vec2((in_vert.x + 1.0) / 2.0, (in_vert.y + 1.0) / 2.0);
                gl_Position = vec4(in_vert, 0.0, 1.0);
            }
            """,
            fragment_shader="""
            #version 330
            in vec2 tex_coord;
            out vec4 fragColor;
            uniform sampler2D background;
            void main() {
                fragColor = texture(background, tex_coord);
            }
            """
        )
        bg_prog['background'] = 0
        vao = self.ctx.simple_vertex_array(bg_prog, quad, 'in_vert')
        vao.render(moderngl.TRIANGLE_STRIP)

        # Render buttons using Pygame
        surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update((mouse_x, mouse_y))
            btn.draw(surface)
        data = pygame.image.tostring(surface, "RGBA", False)
        button_texture = self.ctx.texture((WIDTH, HEIGHT), 4, data)
        button_texture.use(location=1)
        btn_prog = self.ctx.program(
            vertex_shader="""
            #version 330
            in vec2 in_vert;
            out vec2 tex_coord;
            void main() {
                tex_coord = vec2((in_vert.x + 1.0) / 2.0, 1.0 - (in_vert.y + 1.0) / 2.0);
                gl_Position = vec4(in_vert, 0.0, 1.0);
            }
            """,
            fragment_shader="""
            #version 330
            in vec2 tex_coord;
            out vec4 fragColor;
            uniform sampler2D button_texture;
            void main() {
                fragColor = texture(button_texture, tex_coord);
            }
            """
        )
        btn_prog['button_texture'] = 1
        vao_buttons = self.ctx.simple_vertex_array(btn_prog, quad, 'in_vert')
        vao_buttons.render(moderngl.TRIANGLE_STRIP)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            for btn in self.buttons:
                if btn.is_clicked((mouse_x, mouse_y), pygame.mouse.get_pressed()):
                    if btn.text.lower() == "exit game":
                        raise SystemExit("Exit Game button pressed")
                    return btn.text
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                raise SystemExit(FORCE_CRASH_MSG)
        return None

# --- Start Menu Section ---
class StartMenu:
    def __init__(self, ctx):
        self.ctx = ctx
        self.font = pygame.font.Font(None, 36)
        # Car selection
        car_dir = os.path.join("assets", "cars")
        self.cars = [f for f in os.listdir(car_dir) if f.lower().endswith('.glb')]
        self.car_dir = car_dir
        self.selected_car = 0 if self.cars else -1
        # Level selection
        self.level_dir = "levels"
        self.levels = self._get_levels()
        self.selected_level = 0 if self.levels else -1
        self.level_rects = []
        # 3D preview setup
        self.preview_size = (180, 100)
        self.preview_fbo = self.ctx.framebuffer(
            color_attachments=[self.ctx.texture(self.preview_size, 4)]
        )
        self.preview_prog = None
        self.preview_scene = None
        self._load_car_preview()

    def _get_levels(self):
        return sorted([f for f in os.listdir(self.level_dir) if f.lower().endswith('.json')])

    def _load_car_preview(self):
        # Load the selected car's .glb model for preview
        if self.cars and self.selected_car >= 0:
            car_path = os.path.join(self.car_dir, self.cars[self.selected_car])
            try:
                # Register the car directory for moderngl_window resource loader
                register_dir(Path(self.car_dir))
                # Load the scene using moderngl_window's SceneLoader
                from moderngl_window.scene import Scene
                self.preview_scene = Scene.from_file(self.cars[self.selected_car])
                # Simple shader for preview
                self.preview_prog = self.ctx.program(
                    vertex_shader="""
                    #version 330
                    uniform mat4 m_proj;
                    uniform mat4 m_view;
                    in vec3 in_position;
                    in vec3 in_normal;
                    out vec3 v_normal;
                    void main() {
                        v_normal = in_normal;
                        gl_Position = m_proj * m_view * vec4(in_position, 1.0);
                    }
                    """,
                    fragment_shader="""
                    #version 330
                    in vec3 v_normal;
                    out vec4 fragColor;
                    void main() {
                        float light = dot(normalize(v_normal), normalize(vec3(0.5, 1.0, 1.0))) * 0.5 + 0.5;
                        fragColor = vec4(vec3(0.2, 0.7, 1.0) * light, 1.0);
                    }
                    """
                )
            except Exception as e:
                self.preview_scene = None
                self.preview_prog = None
        else:
            self.preview_scene = None
            self.preview_prog = None

    def render(self):
        surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        surface.fill((10, 20, 60))
        # Level selection (top left)
        pygame.draw.rect(surface, (40, 40, 80, 220), (40, 80, 400, HEIGHT-160))
        level_title = self.font.render("Level Selection", True, (255,255,255))
        surface.blit(level_title, (60, 100))
        self.level_rects = []
        for idx, lvl in enumerate(self.levels):
            color = (0,255,0) if idx == self.selected_level else (200,200,200)
            lvl_text = self.font.render(lvl, True, color)
            y = 150 + idx*40
            surface.blit(lvl_text, (80, y))
            rect = pygame.Rect(80, y, lvl_text.get_width(), lvl_text.get_height())
            self.level_rects.append(rect)
        # Car selection (bottom right, moved up for more space)
        car_box_w, car_box_h = 400, 220
        car_box_x = WIDTH - car_box_w - 40
        car_box_y = HEIGHT - car_box_h - 120
        pygame.draw.rect(surface, (30, 30, 90, 220), (car_box_x, car_box_y, car_box_w, car_box_h))
        car_title = self.font.render("Car Selection", True, (255,255,255))
        surface.blit(car_title, (car_box_x + 20, car_box_y + 20))
        # Car preview and arrows
        preview_x = car_box_x + car_box_w // 2
        preview_y = car_box_y + car_box_h // 2 + 10
        arrow_color = (255, 255, 0)
        # Draw left arrow
        pygame.draw.polygon(surface, arrow_color, [
            (preview_x - 110, preview_y),
            (preview_x - 80, preview_y - 20),
            (preview_x - 80, preview_y + 20)
        ])
        # Draw right arrow
        pygame.draw.polygon(surface, arrow_color, [
            (preview_x + 110, preview_y),
            (preview_x + 80, preview_y - 20),
            (preview_x + 80, preview_y + 20)
        ])
        # Draw car 3D model preview
        if self.preview_scene and self.preview_prog:
            self.preview_fbo.use()
            self.ctx.clear(0.1, 0.1, 0.1, 1.0)
            aspect = self.preview_size[0] / self.preview_size[1]
            from pyrr import Matrix44
            proj = Matrix44.perspective_projection(45.0, aspect, 0.1, 100.0)
            view = Matrix44.look_at(
                (0, 0.5, 2.2),  # camera position
                (0, 0.3, 0),    # look at
                (0, 1, 0)       # up
            )
            self.preview_prog['m_proj'].write(proj.astype('f4').tobytes())
            self.preview_prog['m_view'].write(view.astype('f4').tobytes())
            for mesh in self.preview_scene.meshes:
                mesh.vao.render(self.preview_prog)
            # Read pixels and blit to main surface
            data = self.preview_fbo.read(components=4, alignment=1)
            img = pygame.image.frombuffer(data, self.preview_size, "RGBA")
            img = pygame.transform.flip(img, False, True)
            img_rect = img.get_rect(center=(preview_x, preview_y))
            surface.blit(img, img_rect)
        elif self.cars and self.selected_car >= 0:
            # fallback: gray box and filename
            model_box = pygame.Rect(preview_x-90, preview_y-50, 180, 100)
            pygame.draw.rect(surface, (120,120,120), model_box)
            model_text = self.font.render("3D Preview", True, (0,0,0))
            surface.blit(model_text, (model_box.centerx - model_text.get_width()//2, model_box.centery - model_text.get_height()//2))
        # Draw car file name under preview
        if self.cars and self.selected_car >= 0:
            car_name = self.cars[self.selected_car]
            car_text = self.font.render(car_name, True, (255,255,0))
            text_rect = car_text.get_rect(center=(preview_x, car_box_y + car_box_h - 30))
            surface.blit(car_text, text_rect)
        # Instructions
        inst = self.font.render("Use UP/DOWN or click to select level, LEFT/RIGHT for car, ENTER to confirm, ESC to go back", True, (255,255,255))
        surface.blit(inst, (WIDTH//2 - inst.get_width()//2, HEIGHT-40))
        # Blit to OpenGL
        data = pygame.image.tostring(surface, "RGBA", False)
        tex = self.ctx.texture((WIDTH, HEIGHT), 4, data)
        tex.use(location=1)
        quad = self.ctx.buffer(
            struct.pack('8f', -1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0)
        )
        prog = self.ctx.program(
            vertex_shader="""
            #version 330
            in vec2 in_vert;
            out vec2 tex_coord;
            void main() {
                tex_coord = vec2((in_vert.x + 1.0) / 2.0, 1.0 - (in_vert.y + 1.0) / 2.0);
                gl_Position = vec4(in_vert, 0.0, 1.0);
            }
            """,
            fragment_shader="""
            #version 330
            in vec2 tex_coord;
            out vec4 fragColor;
            uniform sampler2D button_texture;
            void main() {
                fragColor = texture(button_texture, tex_coord);
            }
            """
        )
        prog['button_texture'] = 1
        vao = self.ctx.simple_vertex_array(prog, quad, 'in_vert')
        vao.render(moderngl.TRIANGLE_STRIP)

    def handle_event(self, event):
        self.levels = self._get_levels()
        if self.selected_level >= len(self.levels):
            self.selected_level = len(self.levels) - 1 if self.levels else -1
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                if self.selected_level > 0:
                    self.selected_level -= 1
                elif self.selected_level == 0 and self.levels:
                    self.selected_level = len(self.levels) - 1
            elif event.key == pygame.K_DOWN:
                if self.selected_level < len(self.levels) - 1:
                    self.selected_level += 1
                elif self.selected_level == len(self.levels) - 1 and self.levels:
                    self.selected_level = 0
            elif event.key == pygame.K_LEFT:
                if self.selected_car > 0:
                    self.selected_car -= 1
                    self._load_car_preview()
            elif event.key == pygame.K_RIGHT:
                if self.selected_car < len(self.cars)-1:
                    self.selected_car += 1
                    self._load_car_preview()
            elif event.key == pygame.K_RETURN:
                return ("start_game", self.cars[self.selected_car] if self.selected_car >= 0 else None,
                        self.levels[self.selected_level] if self.selected_level >= 0 else None)
            elif event.key == pygame.K_ESCAPE:
                return "back"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            for idx, rect in enumerate(self.level_rects):
                if rect.collidepoint(mouse_x, mouse_y):
                    self.selected_level = idx
                    break
        return None

# --- Physics Section ---
class Physics:
    @staticmethod
    def calculate_turning_radius(speed, is_drifting):
        base_radius = 10.0
        drift_modifier = 0.5 if is_drifting else 1.0
        return base_radius * drift_modifier / max(speed, 1)

# --- Player Section ---
class Player:
    def __init__(self):
        self.turning = False
        self.turn_start_time = None
        self.speed_gain_bug_active = False

    def update_turning(self, is_turning):
        if is_turning:
            if not self.turning:
                self.turn_start_time = time.time()
                self.turning = True
            elif time.time() - self.turn_start_time > 5:
                self.speed_gain_bug_active = True
        else:
            self.turning = False
            self.turn_start_time = None
            self.speed_gain_bug_active = False
# --- Audio Section ---

# --- Ingame Section ---
class Ingame:
    def __init__(self):
        self.paused = False

    def toggle_pause(self):
        self.paused = not self.paused

# --- Menu/Event Handling Section ---
def handle_menu_events(current_menu, main_menu):
    """
    Handles menu-related events and returns the updated menu state.
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return "quit"
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                debug_log(FORCE_CRASH_MSG)
                raise SystemExit(FORCE_CRASH_MSG)
        elif current_menu == "main":
            menu_action = main_menu.handle_event(event)
            if menu_action:
                debug_log(f"Menu action triggered: {menu_action}")
                return menu_action
    return current_menu

def render_placeholder_menu(current_menu, font):
    """
    Renders a placeholder screen for non-main menus.
    """
    debug_log(f"Rendering {current_menu} menu")
    surface = pygame.display.get_surface()
    surface.fill((50, 50, 50))
    menu_titles = {
        "settings": "Settings",
        "map_selection": "Map Selection",
        "car_selection": "Car Selection"
    }
    text_str = menu_titles.get(current_menu, "Unknown Menu")
    text = font.render(text_str, True, (255, 255, 255))
    surface.blit(text, ((WIDTH - text.get_width()) // 2, (HEIGHT - text.get_height()) // 2))

# --- Main Loop Section ---
def main():
    pygame.init()
    pygame.font.init()
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
    ctx = moderngl.create_context()

    main_menu = MainMenu(ctx)
    start_menu = StartMenu(ctx)
    clock = pygame.time.Clock()
    running = True
    current_menu = "main"
    font = pygame.font.Font(None, 72)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    debug_log(FORCE_CRASH_MSG)
                    raise SystemExit(FORCE_CRASH_MSG)
            elif current_menu == "main":
                menu_action = main_menu.handle_event(event)
                if menu_action:
                    debug_log(f"Menu action triggered: {menu_action}")
                    if menu_action == "Start":
                        current_menu = "start_menu"
                    else:
                        current_menu = menu_action
            elif current_menu == "start_menu":
                result = start_menu.handle_event(event)
                if result:
                    if result == "back":
                        current_menu = "main"
                    elif isinstance(result, tuple) and result[0] == "start_game":
                        # You can launch the game here with result[1] (car) and result[2] (level)
                        pass

        if current_menu == "main":
            debug_log("Rendering main menu")
            main_menu.render()
        elif current_menu == "start_menu":
            start_menu.render()
        else:
            debug_log(f"Rendering {current_menu} menu")
            # Render a placeholder screen for each menu
            surface = pygame.display.get_surface()
            surface.fill((50, 50, 50))
            if current_menu == "settings":
                text = font.render("Settings", True, (255, 255, 255))
            elif current_menu == "map_selection":
                text = font.render("Map Selection", True, (255, 255, 255))
            elif current_menu == "car_selection":
                text = font.render("Car Selection", True, (255, 255, 255))
            else:
                text = font.render("Unknown Menu", True, (255, 255, 255))
            surface.blit(text, ((WIDTH - text.get_width()) // 2, (HEIGHT - text.get_height()) // 2))

        pygame.display.flip()
        clock.tick(60)
        debug_log("Frame rendered")

    pygame.quit()

if __name__ == "__main__":
    main()