import sys
from generate_landscape import generate_landscape

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <output_path> [biome_name]")
        sys.exit(1)
    biome_arg = sys.argv[2] if len(sys.argv) > 2 else None
    generate_landscape(sys.argv[1], biome_arg)
