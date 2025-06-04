import json
import os

def generate_enclosed_map_json(
    width=20, height=15, 
    wall_tile=1, empty_tile=0, 
    out_path="levels/enclosed_generated.json"
):
    """
    Generates an enclosed rectangular map and saves it as a JSON file.
    The map will have walls (wall_tile) around the edges and empty space (empty_tile) inside.
    """
    # Create the 2D grid
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            if x == 0 or x == width-1 or y == 0 or y == height-1:
                row.append(wall_tile)
            else:
                row.append(empty_tile)
        grid.append(row)

    # Example metadata, adjust as needed for your game
    map_data = {
        "name": "Enclosed Generated Map",
        "width": width,
        "height": height,
        "tiles": grid,
        "start": {"x": width // 2, "y": height // 2}
    }

    # Ensure the levels directory exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Write to file
    with open(out_path, "w") as f:
        json.dump(map_data, f, indent=2)
    print(f"Map saved to {out_path}")

def load_map(file_path):
    """
    Load the map file and parse its contents to generate the racetrack.
    :param file_path: Path to the map file (JSON format).
    :return: Parsed map data (e.g., track layout, obstacles, etc.).
    """
    if not file_path or not file_path.endswith(".json"):
        raise ValueError("Invalid map file path provided.")
    
    with open(file_path, 'r') as f:
        map_data = json.load(f)
    
    # Example structure: map_data contains track layout, checkpoints, etc.
    return map_data

def generate_world(map_data):
    """
    Generate the world based on the parsed map data.
    :param map_data: Parsed map data from the JSON file.
    :return: World representation (e.g., track, obstacles, etc.).
    """
    world = {
        "track": map_data.get("track", []),
        "checkpoints": map_data.get("checkpoints", []),
        "obstacles": map_data.get("obstacles", [])
    }
    return world

if __name__ == "__main__":
    generate_enclosed_map_json()