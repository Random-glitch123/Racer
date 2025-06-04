import os
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

class Renderer:
    """
    Renderer class for handling OpenGL rendering.
    Includes methods for rendering the skybox, ground, and custom meshes.
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._grass_texture = None

    # --- Texture Loading ---
    def load_texture(self, file_path):
        """
        Load a texture from a file and return the OpenGL texture ID.
        Converts unsupported formats to a compatible format if necessary.
        :param file_path: Path to the texture file.
        :return: OpenGL texture ID.
        """
        try:
            surface = pygame.image.load(file_path)
            if surface.get_bytesize() not in [3, 4]:  # Check for unsupported formats
                temp_path = os.path.join("temp_texture.png")
                pygame.image.save(surface, temp_path)  # Save as a compatible format
                surface = pygame.image.load(temp_path)  # Reload the converted texture
            texture_data = pygame.image.tostring(surface, "RGBA", True)
            width, height = surface.get_size()
            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            return texture_id
        except Exception as e:
            print(f"Error loading texture {file_path}: {e}")
            return None

    # --- Ground Rendering ---
    def render_ground(self):
        """
        Render the ground using the grass texture.
        """
        if not self._grass_texture:
            grass_texture_path = os.path.join("assets", "textures", "grass.png")  # Ensure correct file name
            self._grass_texture = self.load_texture(grass_texture_path)
            if not self._grass_texture:
                print(f"Error: Failed to load grass texture from {grass_texture_path}.")
                return  # Exit rendering if texture is missing

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self._grass_texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-1000, -1000, 0)
        glTexCoord2f(1, 0); glVertex3f(1000, -1000, 0)
        glTexCoord2f(1, 1); glVertex3f(1000, 1000, 0)
        glTexCoord2f(0, 1); glVertex3f(-1000, 1000, 0)
        glEnd()
        glDisable(GL_TEXTURE_2D)

    # --- Skybox Rendering ---
    def render_skybox(self, camera_position):
        """
        Render the skybox around the camera.
        :param camera_position: Position of the camera.
        """
        # Example implementation for rendering a skybox
        glPushMatrix()
        glTranslatef(*camera_position)
        glBegin(GL_QUADS)
        # Define vertices and texture coordinates for the skybox
        glEnd()
        glPopMatrix()

    # --- Custom Mesh Rendering ---
    def render_custom_mesh(self, vertices, faces, position, rotation, scale):
        """
        Render a custom mesh using vertices and faces.
        :param vertices: List of vertex positions.
        :param faces: List of face indices.
        :param position: Position of the mesh.
        :param rotation: Rotation of the mesh.
        :param scale: Scale of the mesh.
        """
        glPushMatrix()
        glTranslatef(*position)
        glRotatef(rotation[0], 1, 0, 0)
        glRotatef(rotation[1], 0, 1, 0)
        glRotatef(rotation[2], 0, 0, 1)
        glScalef(*scale)
        glBegin(GL_TRIANGLES)
        for face in faces:
            for vertex_index in face:
                glVertex3fv(vertices[vertex_index])
        glEnd()
        glPopMatrix()

    # --- Utility Methods ---
    def clear_screen(self):
        """
        Clear the screen for rendering.
        """
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def set_3d_mode(self):
        """
        Set OpenGL to 3D rendering mode.
        """
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, self.width / self.height, 0.1, 1000)
        glMatrixMode(GL_MODELVIEW)

    def set_2d_mode(self):
        """
        Set OpenGL to 2D rendering mode.
        """
        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)

    def update_display(self):
        """
        Update the OpenGL display.
        """
        pygame.display.flip()