import os
import sys
import time
import math
import random
import signal

# Terminal Control Sequences
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
ALT_BUFFER = "\x1b[?1049h"
NORMAL_BUFFER = "\x1b[?1049l"
CLEAR_SCREEN = "\x1b[2J"
HOME_CURSOR = "\x1b[H"
RESET_COLOR = "\x1b[0m"
UPPER_HALF_BLOCK = "▀"

class Palette:
    def __init__(self, sky_top, sky_bottom, far_mount, mid_mount, ground, sun, stars):
        self.sky_top = sky_top
        self.sky_bottom = sky_bottom
        self.far_mount = far_mount
        self.mid_mount = mid_mount
        self.ground = ground
        self.sun = sun
        self.stars = stars

DAY_PALETTE = Palette(
    sky_top=(60, 140, 255),
    sky_bottom=(180, 220, 255),
    far_mount=(100, 130, 160),
    mid_mount=(60, 90, 80),
    ground=(40, 120, 40),
    sun=(255, 255, 200),
    stars=0.0  # opacity
)

NIGHT_PALETTE = Palette(
    sky_top=(5, 5, 20),
    sky_bottom=(20, 10, 40),
    far_mount=(20, 30, 50),
    mid_mount=(10, 20, 30),
    ground=(5, 15, 10),
    sun=(200, 220, 255), # moon
    stars=1.0  # opacity
)

def lerp_color(c1, c2, t):
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t)
    )

def lerp_palette(p1, p2, t):
    return Palette(
        sky_top=lerp_color(p1.sky_top, p2.sky_top, t),
        sky_bottom=lerp_color(p1.sky_bottom, p2.sky_bottom, t),
        far_mount=lerp_color(p1.far_mount, p2.far_mount, t),
        mid_mount=lerp_color(p1.mid_mount, p2.mid_mount, t),
        ground=lerp_color(p1.ground, p2.ground, t),
        sun=lerp_color(p1.sun, p2.sun, t),
        stars=p1.stars + (p2.stars - p1.stars) * t
    )

class AnimatedWorld:
    def __init__(self):
        self.running = True
        self.t = 0.0
        # Pre-generate some pseudo-random heightmaps for parallax layers
        self.mountains_far = [self._noise(i * 0.05) * 0.3 + 0.4 for i in range(2000)]
        self.mountains_mid = [self._noise(i * 0.1) * 0.4 + 0.6 for i in range(2000)]
        self.ground_layer = [self._noise(i * 0.2) * 0.1 + 0.85 for i in range(2000)]
        
        self.clouds = [self._noise(i * 0.03) for i in range(2000)]
        self.wind_lines = [[random.random(), random.random(), random.random()] for _ in range(15)]

    def _noise(self, x):
        return (math.sin(x) + math.sin(x * 2.5) * 0.5 + math.sin(x * 5.1) * 0.25) / 1.75

    def cleanup(self):
        sys.stdout.write(NORMAL_BUFFER + SHOW_CURSOR + RESET_COLOR)
        sys.stdout.flush()

    def signal_handler(self, sig, frame):
        self.running = False

    def run(self):
        # Setup terminal
        sys.stdout.write(ALT_BUFFER + HIDE_CURSOR)
        sys.stdout.flush()
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        target_fps = 30
        frame_time = 1.0 / target_fps

        try:
            while self.running:
                start_t = time.time()
                self.render_frame()
                elapsed = time.time() - start_t
                if elapsed < frame_time:
                    time.sleep(frame_time - elapsed)
                self.t += 0.05
        finally:
            self.cleanup()

    def render_frame(self):
        cols, rows = os.get_terminal_size()
        width = cols
        height = rows * 2 # Two logic pixels per terminal line
        
        # Calculate day/night cycle
        # Map sin(t * 0.05) from [-1, 1] to [0, 1]
        cycle = (math.sin(self.t * 0.05) + 1.0) / 2.0
        current_palette = lerp_palette(NIGHT_PALETTE, DAY_PALETTE, cycle)
        
        # Buffer to hold RGB tuples
        # Initialize with sky color (gradient)
        buffer = []
        for y in range(height):
            ratio = y / height
            sky_col = lerp_color(current_palette.sky_top, current_palette.sky_bottom, ratio)
            row = [sky_col] * width
            buffer.append(row)
            
        # Draw celestial body (Sun/Moon)
        celestial_y = int(height * 0.3 + math.cos(self.t * 0.05) * height * 0.2)
        celestial_x = int(width * 0.5 + math.sin(self.t * 0.05) * width * 0.4)
        radius = int(width * 0.05)
        for y in range(max(0, celestial_y - radius), min(height, celestial_y + radius)):
            for x in range(max(0, celestial_x - radius), min(width, celestial_x + radius)):
                if (x - celestial_x)**2 + (y - celestial_y)**2 < radius**2:
                    buffer[y][x] = current_palette.sun

        # Draw clouds
        cloud_color = lerp_color((180, 180, 200), (255, 255, 255), cycle)
        cloud_offset = self.t * 3.0
        for x in range(width):
            c_val = self.clouds[int((x + cloud_offset) % 2000)]
            if c_val > 0.65:
                cloud_height = int((c_val - 0.65) * 40)
                base_y = int(height * 0.2)
                for y in range(max(0, base_y - cloud_height), min(height, base_y + cloud_height)):
                    buffer[y][x] = lerp_color(buffer[y][x], cloud_color, 0.8)

        # Draw layers (Static)
        self._draw_parallax_layer(buffer, width, height, self.mountains_far, current_palette.far_mount, 0)
        self._draw_parallax_layer(buffer, width, height, self.mountains_mid, current_palette.mid_mount, 0)
        self._draw_parallax_layer(buffer, width, height, self.ground_layer, current_palette.ground, 0)

        # Draw wind (fast moving horizontal dashed lines)
        wind_color = lerp_color((100, 100, 150), (200, 220, 255), cycle)
        for w in self.wind_lines:
            w[0] = (w[0] + 0.05 * w[2] + 0.02) % 1.0 # x position
            w[1] = (w[1] + math.sin(self.t + w[2]*10) * 0.002) % 1.0 # subtle y wobble
            
            px = int(w[0] * width)
            py = int(w[1] * height)
            
            # Draw lines mainly in the lower half over the terrain
            if py > height * 0.3:
                length = int(w[2] * 8 + 4)
                for i in range(length):
                    if 0 <= px - i < width and 0 <= py < height:
                        bg = buffer[py][px-i]
                        # subtle blend so wind is somewhat transparent
                        buffer[py][px-i] = lerp_color(bg, wind_color, 0.4)

        self._flush_to_terminal(buffer, width, rows)

    def _draw_parallax_layer(self, buffer, width, height, heightmap, color, offset):
        hm_len = len(heightmap)
        for x in range(width):
            # map x + offset to heightmap index
            idx = int((x + offset) % hm_len)
            h_val = heightmap[idx]
            y_start = int(h_val * height)
            for y in range(max(0, y_start), height):
                buffer[y][x] = color

    def _flush_to_terminal(self, buffer, width, rows):
        # Build one giant ANSI string
        # To avoid massive flickering, we use HOME_CURSOR instead of CLEAR_SCREEN
        out = [HOME_CURSOR]
        
        last_fg = None
        last_bg = None
        
        for r in range(rows):
            y_top = r * 2
            y_bottom = r * 2 + 1
            
            for x in range(width):
                fg = buffer[y_top][x]
                if y_bottom < len(buffer):
                    bg = buffer[y_bottom][x]
                else:
                    bg = (0, 0, 0)
                
                if fg != last_fg:
                    out.append(f"\x1b[38;2;{fg[0]};{fg[1]};{fg[2]}m")
                    last_fg = fg
                
                if bg != last_bg:
                    out.append(f"\x1b[48;2;{bg[0]};{bg[1]};{bg[2]}m")
                    last_bg = bg
                    
                out.append(UPPER_HALF_BLOCK)
                
            # Need to clear remaining line just in case, but we fill width anyway.
            # Reset at end of line to prevent terminal weirdness on resize
            out.append(RESET_COLOR + "\n")
            last_fg = None
            last_bg = None

        sys.stdout.write("".join(out))
        sys.stdout.flush()

if __name__ == "__main__":
    world = AnimatedWorld()
    world.run()
