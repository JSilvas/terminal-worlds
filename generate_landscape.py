import random
import math
import sys
from PIL import Image, ImageDraw

# Configuration
WIDTH = 480
HEIGHT = 270
SCALE = 4 

def random_seed():
    seed = random.randrange(sys.maxsize)
    random.seed(seed)
    return seed

# --- NOISE ENGINE ---
class SmoothNoise:
    def __init__(self, seed):
        self.seed = seed
        self.r = random.Random(seed)
            
    def fade(self, t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    def lerp(self, t, a, b):
        return a + t * (b - a)

    def noise2d(self, x, y):
        X = int(math.floor(x))
        Y = int(math.floor(y))
        x -= math.floor(x)
        y -= math.floor(y)
        u = self.fade(x)
        v = self.fade(y)
        
        def val(ix, iy):
            # A more robust mixing hash to prevent lattice artifacts/striping
            h = (self.seed + ix * 374761393 + iy * 668265263) & 0x7fffffff
            h = (h ^ (h >> 13)) * 1274126177
            h = (h ^ (h >> 16)) & 0x7fffffff
            return (1.0 - h / 1073741824.0)

        aa = val(X, Y)
        ab = val(X, Y+1)
        ba = val(X+1, Y)
        bb = val(X+1, Y+1)
        
        res = self.lerp(v, self.lerp(u, aa, ba), self.lerp(u, ab, bb))
        return (res + 1.0) / 2.0 

    def fractal2d(self, x, y, octaves=4, persistence=0.5, rigid=False):
        total = 0
        freq = 1
        amp = 1
        max_val = 0
        for _ in range(octaves):
            n = self.noise2d(x * freq, y * freq)
            if rigid:
                n = abs(n - 0.5) * 2 
                n = 1.0 - n 
                n = n * n 
            total += n * amp
            max_val += amp
            amp *= persistence
            freq *= 2
        return total / max_val

NOISE = None

class Palette:
    def __init__(self, name, sky_top, sky_bottom, far_mount, mid_mount, ground_dark, ground_light, accent, cloud_color, vine_color, water_color, sun_color, moon, structure_base, rune_color, strata_colors, liquid_type='water'):
        self.name = name
        self.sky_top = sky_top
        self.sky_bottom = sky_bottom
        self.far_mount = far_mount
        self.mid_mount = mid_mount
        self.ground_dark = ground_dark
        self.ground_light = ground_light
        self.accent = accent
        self.cloud_color = cloud_color
        self.vine_color = vine_color
        self.water_color = water_color
        self.sun_color = sun_color
        self.moon = moon 
        self.structure_base = structure_base
        self.rune_color = rune_color
        self.strata_colors = strata_colors
        self.liquid_type = liquid_type

BIOMES = [
    # Forest - Day
    Palette(
        "forest",
        (100, 180, 255), (200, 240, 255),   
        (130, 150, 180),                   
        (90, 110, 100),                     
        (50, 40, 30), (34, 150, 34),        # Ground
        (120, 80, 40),                     
        (255, 255, 255),                   
        (40, 140, 40),
        (60, 160, 220), 
        (255, 255, 200), 
        False,
        (80, 80, 90), # Grey Structure
        (0, 255, 255), # Cyan Runes
        [(60, 50, 40), (75, 65, 55), (90, 80, 70)] # Strata
    ),
    # Sunset Desert
    Palette(
        "desert",
        (100, 40, 80), (255, 150, 80),     
        (180, 100, 80),                    
        (160, 80, 50),                     
        (80, 30, 10), (220, 160, 60),      
        (100, 100, 110),                   
        (255, 200, 180),                   
        (100, 110, 60),
        (240, 120, 60), 
        (255, 100, 50), 
        False,
        (140, 100, 80), # Sandstone
        (255, 215, 0),   # Gold Runes
        [(140, 70, 40), (160, 90, 60), (180, 110, 80)] # Strata
    ),
     # Corruption - Night
    Palette(
        "corruption",
        (10, 0, 20), (50, 20, 70),         
        (50, 40, 70),                      
        (50, 30, 60),                      
        (25, 10, 25), (100, 80, 140),      
        (80, 80, 90),                      
        (80, 70, 90),                      
        (70, 0, 90),
        (80, 0, 140), 
        (200, 230, 255), 
        True,
        (40, 40, 50), # Dark Stone
        (50, 255, 100), # Toxic Green Runes
        [(40, 20, 50), (30, 15, 40), (50, 30, 70)] # Strata
    ),
    # Volcanic - Obsidian/Lava
    Palette(
        "volcanic",
        (20, 10, 10), (80, 30, 20),         # Dark red sky
        (50, 40, 40),                      # Brighter dark mts
        (40, 30, 30),                      
        (45, 40, 45), (100, 100, 110),      # MUCH brighter starting colors
        (220, 80, 40),                     # Stronger glow accent
        (120, 60, 50),                     # Ash clouds
        (130, 50, 30),
        (255, 90, 20),                     # Lava
        (255, 170, 70), 
        True,
        (55, 50, 50), # Basalt
        (255, 140, 0), # Lava Runes
        [(30, 25, 25), (45, 40, 40), (55, 50, 50)], # Strata
        liquid_type='lava'
    )
]

def draw_tree(draw, x, y, size, angle, depth, color, seed, leaf_color):
    if depth == 0 or size < 1:
        return

    r = random.Random(seed + depth + x + y)
    length = size * (0.8 + r.random() * 0.4)
    end_x = x + int(length * math.sin(angle))
    end_y = y - int(length * math.cos(angle))
    
    width = max(1, int(depth * 0.7))
    draw.line([(x, y), (end_x, end_y)], fill=color, width=width)
    
    num = r.randint(1, 4) if depth > 2 else r.randint(1,3)
    for i in range(num):
        new_angle = angle + (r.random() - 0.5) * 1.5 
        new_size = size * 0.75
        draw_tree(draw, end_x, end_y, new_size, new_angle, depth - 1, color, seed + i*20, leaf_color)
        
    if depth <= 2:
        # Voluminous leaf clusters
        r_leaf = r.randint(3, 6)
        num_leaves = r.randint(6, 12)
        for _ in range(num_leaves):
            lx = end_x + r.randint(-r_leaf, r_leaf)
            ly = end_y + r.randint(-r_leaf, r_leaf)
            
            l_col = (
                min(255, max(0, leaf_color[0] + r.randint(-20, 20))),
                min(255, max(0, leaf_color[1] + r.randint(-20, 20))),
                min(255, max(0, leaf_color[2] + r.randint(-20, 20)))
            )
            # Use small blocks/pixels for clusters
            if r.random() < 0.3:
                draw.rectangle([lx, ly, lx+1, ly+1], fill=l_col)
            else:
                draw.point((lx, ly), fill=l_col)

def draw_ground_cover(draw, x, y, biome, r):
    # Specialized flora based on biome colors
    if biome.sun_color == (255, 100, 50) and r.random() < 0.2:
        draw_cactus(draw, x, y, r)
        return
    if biome.sun_color == (200, 230, 255) and r.random() < 0.3:
        draw_biolume(draw, x, y, r)
        return

    # Draw small grass clumps or pebbles
    if biome.liquid_type == 'lava':
        # Pebbles/Ash patches for volcanic
        num_pebbles = r.randint(2, 5)
        for _ in range(num_pebbles):
            px = x + r.randint(-3, 3)
            py = y - r.randint(0, 2)
            if px >= 0 and px < WIDTH and py >= 0 and py < HEIGHT:
                draw.point((px, py), fill=biome.ground_dark)
    else:
        # Flora Variety Pass
        if r.random() < 0.15:
            variety = r.random()
            if variety < 0.4:
                draw_fern(draw, x, y, r, biome.vine_color)
            elif variety < 0.7:
                draw_shrub(draw, x, y, r, biome.vine_color, biome.accent)
            else:
                draw_sapling(draw, x, y, r, biome.ground_dark, biome.vine_color)
            return

        # Lush contiguous Ground Carpet
        num_clumps = r.randint(2, 4)
        for _ in range(num_clumps):
            cx = x + r.randint(-2, 2)
            cw = r.randint(2, 5) # Clump width
            for ox in range(cw):
                bx = cx + ox
                if bx < 0 or bx >= WIDTH: continue
                # Height variance for natural look
                bh = r.randint(2, 5)
                f_col = get_variant_color(biome.vine_color, r)
                for i in range(bh):
                    by = y - i
                    if by >= 0 and by < HEIGHT:
                        draw.point((bx, by), fill=f_col)

def draw_overhanging_flora(draw, x, y, biome, r):
    if biome.liquid_type == 'lava': return # Lava cliffs are bare
    
    num_strands = r.randint(3, 8)
    for _ in range(num_strands):
        ox = x + r.randint(-2, 2)
        if ox < 0 or ox >= WIDTH: continue
        
        length = r.randint(3, 10)
        # Tapered or jagged hanging strands
        for i in range(length):
            oy = y + i
            if oy >= 0 and oy < HEIGHT:
                draw.point((ox, oy), fill=biome.vine_color)
                # Random side pixels for width
                if i < length // 2 and r.random() < 0.4:
                    draw.point((ox + (1 if r.random() > 0.5 else -1), oy), fill=biome.vine_color)

def draw_cactus(draw, x, y, r):
    # Procedural multi-armed cactus
    h = r.randint(12, 28)
    w = r.randint(3, 5)
    c_col = (40, 120, 50) # Cactus Green
    # Deep trunk
    draw.rectangle([x-w//2, y-h, x+w//2, y], fill=c_col)
    # Arms
    for _ in range(r.randint(1, 3)):
        ay = y - r.randint(h//3, h-8)
        side = 1 if r.random() > 0.5 else -1
        aw = r.randint(6, 12)
        # horizontal - Ensure x0 <= x1 for PIL
        x0, x1 = (x, x+side*aw) if side == 1 else (x+side*aw, x)
        draw.rectangle([x0, ay-2, x1, ay], fill=c_col)
        # vertical tip
        tx0, tx1 = (x1-2, x1) if side == 1 else (x1, x1+2)
        draw.rectangle([tx0, ay-10, tx1, ay], fill=c_col)

def draw_biolume(draw, x, y, r):
    # Glowing mushrooms/blooms
    h = r.randint(3, 7)
    base_col = (120, 60, 180) # Purple
    glow_col = (50, 255, 180) # Biolume Cyan/Teal
    # Stem
    draw.line([(x, y), (x, y-h)], fill=base_col, width=1)
    # Cap
    rad = r.randint(2, 4)
    draw.ellipse([x-rad, y-h-rad, x+rad, y-h], fill=glow_col)

def draw_moss(pixels, x, y, r, color):
    # Clingy patches for vertical surfaces
    patch_size = r.randint(2, 5)
    for dy in range(patch_size):
        for dx in range(-1, 2):
            px, py = x + dx, y + dy
            if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                if r.random() < 0.7:
                    pixels[px, py] = get_variant_color(color, r, amount=10)

def color_clamp(c):
    return (
        min(255, max(0, int(c[0]))),
        min(255, max(0, int(c[1]))),
        min(255, max(0, int(c[2])))
    )

def get_variant_color(base_col, r, amount=15):
    """Subtly jitters the hue/brightness of a color."""
    return color_clamp((
        base_col[0] + r.randint(-amount, amount),
        base_col[1] + r.randint(-amount, amount),
        base_col[2] + r.randint(-amount, amount)
    ))

def draw_fern(draw, x, y, r, color):
    # Fronds arching left and right
    num_fronds = r.randint(3, 6)
    for _ in range(num_fronds):
        angle = (r.random() - 0.5) * 2.5
        length = r.randint(5, 12)
        f_col = get_variant_color(color, r)
        # Draw a curved line with dots
        for i in range(length):
            t = i / length
            ox = x + int(math.sin(angle) * i * (1+t))
            oy = y - int(math.cos(angle) * i) - int(t * 3)
            if 0 <= ox < WIDTH and 0 <= oy < HEIGHT:
                draw.point((ox, oy), fill=f_col)

def draw_shrub(draw, x, y, r, color, accent):
    # Rounded clump
    rad = r.randint(3, 7)
    for _ in range(30):
        ox = x + int(r.gauss(0, rad * 0.6))
        oy = y - int(abs(r.gauss(0, rad * 0.4)))
        if 0 <= ox < WIDTH and 0 <= oy < HEIGHT:
            f_col = get_variant_color(color, r)
            draw.point((ox, oy), fill=f_col)
            # Occasional flowers
            if r.random() < 0.08:
                draw.point((ox, oy), fill=accent)

def draw_sapling(draw, x, y, r, color, leaf_color):
    h = r.randint(8, 15)
    # Thin trunk
    draw.line([(x, y), (x, y-h)], fill=color, width=1)
    # Minimal leaves at top
    for _ in range(8):
        lx = x + r.randint(-3, 3)
        ly = y - h + r.randint(-3, 1)
        if 0 <= lx < WIDTH and 0 <= ly < HEIGHT:
            draw.point((lx, ly), fill=get_variant_color(leaf_color, r))

def apply_shading(pixels, x, y, width, height, noise_seed, base_color, strength=40.0, ns=0.04, haze=0, sky_color=None):
    # 1. Spatially varying noise scale (Frequency Jitter)
    # This makes some areas look rougher and others broader
    ns_mod = 1.0 + NOISE.fractal2d(x * 0.005, y * 0.005, octaves=1) * 0.4
    local_ns = ns * ns_mod
    
    # 2. Swirled Shading (Flow Fields)
    # Use low-frequency noise to warp the lookup coordinates (Organic Heave)
    warp_x = NOISE.fractal2d(x * 0.01, y * 0.01, octaves=1) * 2.0
    warp_y = NOISE.fractal2d(y * 0.01, x * 0.01 + 100, octaves=1) * 2.0
    
    # Jitter coordinates slightly to break lattice/striping axis alignment
    jx, jy = (x + warp_x) * local_ns + y * 0.01, (y + warp_y) * local_ns + x * 0.01
    
    mat_noise = NOISE.fractal2d(jx, jy, octaves=2)
    mat_noise_right = NOISE.fractal2d(jx + local_ns, jy + 0.01, octaves=2)
    mat_noise_down = NOISE.fractal2d(jx + 0.01, jy + local_ns, octaves=2)
    
    dx = mat_noise_right - mat_noise
    dy = mat_noise_down - mat_noise
    
    # 3. Non-Uniform Shading Direction
    # Vary the light weights to break diagonal "rake marks"
    lw_x = -0.7 + NOISE.fractal2d(x * 0.008, y * 0.008, octaves=1) * 0.5
    lw_y = -0.7 + NOISE.fractal2d(y * 0.008, x * 0.008 + 200, octaves=1) * 0.5
    
    light = (dx * lw_x + dy * lw_y) * strength
    grit = (random.random() - 0.5) * 8
    
    r = base_color[0] + light + grit
    g = base_color[1] + light + grit
    b = base_color[2] + light + grit
    
    if haze > 0 and sky_color:
        r = r * (1 - haze) + sky_color[0] * haze
        g = g * (1 - haze) + sky_color[1] * haze
        b = b * (1 - haze) + sky_color[2] * haze
        
    pixels[x, y] = color_clamp((r, g, b))

# --- STRUCTURE GENERATION ---
def draw_starfield(pixels, width, height, seed, intensity):
    r = random.Random(seed)
    num_stars = int(width * height * 0.002 * intensity) # 0.2% coverage max
    for _ in range(num_stars):
        sx = r.randint(0, width-1)
        sy = r.randint(0, int(height*0.7)) # Don't go too low
        
        # Avoid stars on top of mountains if possible? 
        # Actually easier to just draw them first (which we do)
        
        mag = r.random()
        c = int(150 + mag * 105)
        pixels[sx, sy] = (c, c, c)
        
        if mag > 0.95: # Big star
            if sx+1<width: pixels[sx+1, sy] = (c,c,c)
            if sy+1<height: pixels[sx, sy+1] = (c,c,c)
            if sx-1>=0: pixels[sx-1, sy] = (c//2, c//2, c//2) # Twinkle

def draw_monolith(pixels, x, ground_y, seed, palette):
    """Tall stone pilllar with runes and shape variations"""
    r = random.Random(seed)
    height = r.randint(60, 100)
    width = r.randint(8, 14)
    
    # Expanded shape variety
    shape = r.choice(['obelisk', 'slab', 'totem', 'spire', 'arch', 'twin', 'crystal'])
    
    for py in range(ground_y - height, ground_y + 5):
        for px in range(x - width//2, x + width//2):
            if px < 0 or px >= WIDTH or py < 0 or py >= HEIGHT: continue
            
            # Shape masking
            rel_y = (ground_y - py) / height # 0 at bottom, 1 at top
            rel_x = abs(px - x) / (width/2) # 0 at center, 1 at edge
            
            # Skip pixel based on shape
            skip = False
            if shape == 'obelisk':
                if rel_x > 1.0 - rel_y * 0.5: skip = True # Taper top
            elif shape == 'totem':
                if (int(rel_y * 10) % 2 == 0) and rel_x > 0.8: skip = True # Notches
            elif shape == 'slab':
                if rel_y > 0.9 and rel_x > 0.4: skip = True # Broken top
            elif shape == 'spire':
                if rel_x > 1.0 - rel_y * 0.8: skip = True # Sharp taper
            elif shape == 'arch':
                # Hollow center at top
                if rel_y > 0.6 and rel_y < 0.9 and abs(px - x) < 3: skip = True
            elif shape == 'twin':
                # Two pillars side by side
                if abs(px - x) < 2: skip = True # Gap in middle
                if rel_x > 0.9: skip = True # Narrow each side
            elif shape == 'crystal':
                # Faceted, angular
                facet = int((px - x + rel_y * 10) % 4)
                if facet == 0 and rel_x > 0.7: skip = True
                if rel_y > 0.95: skip = True # Flat top
            
            if skip: continue
            
            # Texture
            noise = r.random() * 20 - 10
            col = (
                int(palette.structure_base[0] + noise),
                int(palette.structure_base[1] + noise),
                int(palette.structure_base[2] + noise)
            )
            
            # Shading based on shape
            if shape == 'crystal':
                # Stronger facet shading
                facet = int((px - x + rel_y * 10) % 4)
                if facet in [0, 1]: col = (col[0]+15, col[1]+15, col[2]+15)
                else: col = (col[0]-15, col[1]-15, col[2]-15)
            else:
                # Standard shading
                if px < x: col = (col[0]+10, col[1]+10, col[2]+10)
                else: col = (col[0]-10, col[1]-10, col[2]-10)
            
            pixels[px, py] = color_clamp(col)
            
            # Runes (more varied placement)
            if r.random() < 0.06 and py < ground_y - 10:
                if shape in ['arch', 'twin']:
                    # Runes on edges for arch/twin
                    if abs(px - x) > 2 and abs(px - x) < 5:
                        pixels[px, py] = palette.rune_color
                else:
                    # Central runes for others
                    if px > x - 2 and px < x + 2:
                        pixels[px, py] = palette.rune_color
                        if r.random() < 0.5: pixels[px, py-1] = palette.rune_color

def draw_ruin(pixels, x, ground_y, seed, palette):
    """Complex ruins"""
    r = random.Random(seed)
    # Generate a layout
    struct_w = r.randint(30, 60)
    struct_h = r.randint(20, 50)
    
    # 2D grid for structure
    grid = [[0 for _ in range(struct_h)] for _ in range(struct_w)]
    
    # Cellular automata for "ruined wall"
    for ix in range(struct_w):
        for iy in range(struct_h):
            grid[ix][iy] = 1 if r.random() > 0.4 else 0
            
    # Smoothing
    for _ in range(2):
        new_grid = [row[:] for row in grid]
        for ix in range(1, struct_w-1):
            for iy in range(1, struct_h-1):
                count = sum([grid[ix+dx][iy+dy] for dx in [-1,0,1] for dy in [-1,0,1]])
                if count > 4: new_grid[ix][iy] = 1
                elif count < 3: new_grid[ix][iy] = 0
        grid = new_grid
        
    start_x = x - struct_w // 2
    
    for ix in range(struct_w):
        h_col = r.randint(struct_h // 2, struct_h) # Variable height
        for iy in range(h_col):
            if grid[ix][iy] == 0: continue
            
            px = start_x + ix
            py = ground_y - iy
            
            if px < 0 or px >= WIDTH or py < 0 or py >= HEIGHT: continue
            
            col = palette.structure_base
            # Noise
            if r.random() < 0.2:
                 col = (col[0]-10, col[1]-10, col[2]-10)
            
            pixels[px, py] = color_clamp(col)

def draw_alien_arch(pixels, x, ground_y, seed, palette):
    """Large alien arch using CA for organic shapes"""
    r = random.Random(seed)
    width = r.randint(50, 80)
    height = r.randint(80, 120)
    
    # Create symmetrical CA grid
    half_w = width // 2
    grid = [[0 for _ in range(height)] for _ in range(half_w)]
    
    # Initialize with arch-like seed
    for ix in range(half_w):
        for iy in range(height):
            rel_y = iy / height
            rel_x = ix / half_w
            # Arch profile: hollow center, solid edges
            if rel_y < 0.3:  # Base
                grid[ix][iy] = 1 if r.random() > 0.3 else 0
            elif rel_y > 0.7:  # Top arch
                if abs(rel_x - 0.5) > 0.2 and abs(rel_x - 0.5) < 0.6:
                    grid[ix][iy] = 1 if r.random() > 0.4 else 0
    
    # CA iterations for organic growth
    for _ in range(3):
        new_grid = [row[:] for row in grid]
        for ix in range(1, half_w-1):
            for iy in range(1, height-1):
                count = sum([grid[ix+dx][iy+dy] for dx in [-1,0,1] for dy in [-1,0,1]])
                if count >= 5: new_grid[ix][iy] = 1
                elif count <= 2: new_grid[ix][iy] = 0
        grid = new_grid
    
    # Draw mirrored
    start_x = x - width // 2
    
    # Ensure grounding: force base row to be solid
    for ix in range(half_w):
        grid[ix][0] = 1
    
    for ix in range(half_w):
        for iy in range(height):
            if grid[ix][iy] == 0: continue
            
            # Left side
            px_left = start_x + ix
            py = ground_y - iy
            # Right side (mirrored)
            px_right = start_x + width - ix - 1
            
            col = palette.structure_base
            noise = r.random() * 15 - 7
            col = (int(col[0]+noise), int(col[1]+noise), int(col[2]+noise))
            
            if px_left >= 0 and px_left < WIDTH and py >= 0 and py < HEIGHT:
                pixels[px_left, py] = color_clamp(col)
            if px_right >= 0 and px_right < WIDTH and py >= 0 and py < HEIGHT:
                pixels[px_right, py] = color_clamp(col)
            
            # Glowing runes on arch top
            if iy > height * 0.7 and r.random() < 0.03:
                if px_left >= 0 and px_left < WIDTH and py >= 0 and py < HEIGHT:
                    pixels[px_left, py] = palette.rune_color

def draw_lattice(pixels, x, ground_y, seed, palette):
    """Delicate lattice structure using CA"""
    r = random.Random(seed)
    width = r.randint(40, 60)
    height = r.randint(60, 90)
    
    grid = [[0 for _ in range(height)] for _ in range(width)]
    
    # Sparse initialization for lattice feel
    for ix in range(width):
        for iy in range(height):
            grid[ix][iy] = 1 if r.random() > 0.7 else 0
    
    # CA for web-like patterns (different rules)
    for _ in range(2):
        new_grid = [row[:] for row in grid]
        for ix in range(1, width-1):
            for iy in range(1, height-1):
                count = sum([grid[ix+dx][iy+dy] for dx in [-1,0,1] for dy in [-1,0,1]])
                # Keep sparse connections
                if count == 3 or count == 4:
                    new_grid[ix][iy] = 1
                elif count < 2 or count > 5:
                    new_grid[ix][iy] = 0
        grid = new_grid
    
    start_x = x - width // 2
    for ix in range(width):
        for iy in range(height):
            if grid[ix][iy] == 0: continue
            
            px = start_x + ix
            py = ground_y - iy
            
            if px < 0 or px >= WIDTH or py < 0 or py >= HEIGHT: continue
            
            # Delicate, lighter color
            col = (
                int(palette.structure_base[0] * 0.8 + 50),
                int(palette.structure_base[1] * 0.8 + 50),
                int(palette.structure_base[2] * 0.8 + 50)
            )
            pixels[px, py] = color_clamp(col)
            
            # Occasional glow nodes
            if r.random() < 0.05:
                pixels[px, py] = palette.rune_color

def draw_multispire(pixels, x, ground_y, seed, palette):
    """Multi-spire alloy tree using CA"""
    r = random.Random(seed)
    width = r.randint(35, 55)
    height = r.randint(90, 130)
    
    grid = [[0 for _ in range(height)] for _ in range(width)]
    
    # Multiple seed points for spires
    num_spires = r.randint(3, 5)
    for _ in range(num_spires):
        spire_x = r.randint(width//4, 3*width//4)
        spire_base_y = r.randint(0, height//4)
        # Vertical seed
        for iy in range(spire_base_y, min(height, spire_base_y + height//2)):
            if spire_x < width:
                grid[spire_x][iy] = 1
                if spire_x > 0: grid[spire_x-1][iy] = 1 if r.random() > 0.5 else 0
                if spire_x < width-1: grid[spire_x+1][iy] = 1 if r.random() > 0.5 else 0
    
    # CA to connect and branch spires
    for _ in range(4):
        new_grid = [row[:] for row in grid]
        for ix in range(1, width-1):
            for iy in range(1, height-1):
                count = sum([grid[ix+dx][iy+dy] for dx in [-1,0,1] for dy in [-1,0,1]])
                # Prefer vertical growth
                if count >= 4 and count <= 6:
                    new_grid[ix][iy] = 1
                elif count < 3:
                    new_grid[ix][iy] = 0
        grid = new_grid
    
    # Ensure grounding: force base row to be solid where there are spires
    for ix in range(width):
        # Check if there's any structure above this column
        has_structure = any(grid[ix][iy] for iy in range(height))
        if has_structure:
            grid[ix][0] = 1
            if ix > 0: grid[ix-1][0] = 1
            if ix < width-1: grid[ix+1][0] = 1
    
    start_x = x - width // 2
    for ix in range(width):
        for iy in range(height):
            if grid[ix][iy] == 0: continue
            
            px = start_x + ix
            py = ground_y - iy
            
            if px < 0 or px >= WIDTH or py < 0 or py >= HEIGHT: continue
            
            # Metallic/crystalline appearance
            col = palette.structure_base
            # Facet-like shading
            facet = int((ix + iy * 0.3) % 5)
            if facet < 2:
                col = (col[0]+20, col[1]+20, col[2]+20)
            else:
                col = (col[0]-10, col[1]-10, col[2]-10)
            
            pixels[px, py] = color_clamp(col)
            
            # Runes on spire tips
            rel_y = iy / height
            if rel_y > 0.8 and r.random() < 0.08:
                pixels[px, py] = palette.rune_color



def draw_lantern(pixels, x, ground_y, seed, palette):
    """Pole with hanging light"""
    r = random.Random(seed)
    height = r.randint(20, 30)
    
    # Pole
    for py in range(ground_y - height, ground_y):
        pixels[x, py] = (50, 40, 30) # Wood color
        
    # Lantern hanging
    ly = ground_y - height + 2
    lx = x + 3
    # Arm
    for px in range(x, lx+1):
        pixels[px, ground_y - height] = (50, 40, 30)
    # Rope
    pixels[lx, ground_y - height + 1] = (20, 20, 20)
    
    # Light
    lc = palette.rune_color # Reuse rune color for light
    pixels[lx, ly] = lc
    pixels[lx+1, ly] = lc
    pixels[lx, ly+1] = lc
    pixels[lx+1, ly+1] = lc
    
    # Glow
    for gy in range(ly-4, ly+5):
        for gx in range(lx-4, lx+5):
             if gx < 0 or gx >= WIDTH or gy < 0 or gy >= HEIGHT: continue
             dist = math.sqrt((gx-lx)**2 + (gy-ly)**2)
             if dist < 4:
                 base = pixels[gx, gy]
                 alpha = 0.3 * (1 - dist/4)
                 pixels[gx, gy] = color_clamp((
                     base[0]*(1-alpha) + lc[0]*alpha,
                     base[1]*(1-alpha) + lc[1]*alpha,
                     base[2]*(1-alpha) + lc[2]*alpha
                 ))


def generate_landscape(output_path, biome_name=None):
    global NOISE
    seed = random_seed()
    NOISE = SmoothNoise(seed)
    
    biome = None
    if biome_name:
        for b in BIOMES:
            if b.name.lower() == biome_name.lower():
                biome = b
                break
    
    if not biome:
        biome = random.choice(BIOMES)
    
    img = Image.new('RGB', (WIDTH, HEIGHT), biome.sky_top)
    draw = ImageDraw.Draw(img)
    pixels = img.load() 
    
    # 1. Sky
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        sky_col = (
            int(biome.sky_top[0] + (biome.sky_bottom[0] - biome.sky_top[0]) * ratio),
            int(biome.sky_top[1] + (biome.sky_bottom[1] - biome.sky_top[1]) * ratio),
            int(biome.sky_top[2] + (biome.sky_bottom[2] - biome.sky_top[2]) * ratio)
        )
        for x in range(WIDTH):
            pixels[x, y] = sky_col

    # 1.5 Starfield (New)
    # Check brightness of sky to decide density
    sky_bri = (biome.sky_top[0] + biome.sky_top[1] + biome.sky_top[2]) / 3.0
    if sky_bri < 100: # Dark sky
        draw_starfield(pixels, WIDTH, HEIGHT, seed, intensity=1.0)
    elif sky_bri < 150: # Twilight
        draw_starfield(pixels, WIDTH, HEIGHT, seed, intensity=0.3)

    # 2. Celestial Body
    cx = random.randint(50, WIDTH - 50)
    cy = random.randint(30, 80)
    # Probabilistic appearance: 75% chance
    celestial_visible = random.random() < 0.75
    
    if celestial_visible:
        rad = random.randint(15, 25)
        for y in range(cy - rad*2, cy + rad*2):
            for x in range(cx - rad*2, cx + rad*2):
                if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT: continue
                dist = math.sqrt((x-cx)**2 + (y-cy)**2)
                if dist < rad: pixels[x, y] = biome.sun_color
                elif dist < rad * 1.5:
                    alpha = (dist - rad) / (rad * 0.5)
                    base = pixels[x, y]
                    glow = biome.sun_color
                    r = base[0] * alpha + glow[0] * (1-alpha)
                    g = base[1] * alpha + glow[1] * (1-alpha)
                    b = base[2] * alpha + glow[2] * (1-alpha)
                    pixels[x, y] = color_clamp((r, g, b))

    # 3. Clouds
    # We use a 2x2 block grid for consistent pixel-art feel
    for x in range(0, WIDTH, 2): 
        for y in range(0, int(HEIGHT * 0.45), 2): # Slightly lower cloud ceiling
            nx, ny = x * 0.015, y * 0.03
            val = NOISE.fractal2d(nx, ny, octaves=3) - NOISE.fractal2d(nx*2+10, ny*2+10, octaves=1)*0.2
            
            if val > 0.60:
                # Main Cloud Color
                c = biome.cloud_color
                
                # ROUNDED SHADING LOGIC
                # Look at neighboring cells to decide if this is a bottom/right edge
                # Offset by 2 because we are in a 2-step loop
                nx_right, ny_right = (x+2) * 0.015, y * 0.03
                nx_down, ny_down = x * 0.015, (y+2) * 0.03
                
                val_right = NOISE.fractal2d(nx_right, ny_right, octaves=3) - NOISE.fractal2d(nx_right*2+10, ny_right*2+10, octaves=1)*0.2
                val_down = NOISE.fractal2d(nx_down, ny_down, octaves=3) - NOISE.fractal2d(nx_down*2+10, ny_down*2+10, octaves=1)*0.2
                
                # It's an edge if neighbors are empty (val < 0.6)
                is_edge = (val_right < 0.60 or val_down < 0.60)
                
                # Deep Shade (Bottom/Right boundaries)
                if is_edge and val > 0.63:
                    c = (max(0, c[0]-35), max(0, c[1]-35), max(0, c[2]-25))
                # Internal Volume (Deeper in the cloud)
                elif val > 0.72:
                    c = (max(0, c[0]-15), max(0, c[1]-15), max(0, c[2]-10))
                
                # Draw 2x2 pixel block
                for dx in range(2):
                    for dy in range(2):
                        px, py = x + dx, y + dy
                        if px < WIDTH and py < HEIGHT:
                            pixels[px, py] = c

    # 4. Far Mountains
    for x in range(WIDTH):
        nx = x / 250.0
        h = NOISE.fractal2d(nx, 0, octaves=4, rigid=True)
        y_start = int(HEIGHT * 0.55 - (h * 90))
        if y_start < HEIGHT:
            for y in range(y_start, HEIGHT):
               # Far layer: High haze (0.22)
               apply_shading(pixels, x, y, WIDTH, HEIGHT, seed, biome.far_mount, strength=25.0, ns=0.03, haze=0.22, sky_color=biome.sky_bottom)

    # 5. Mid Mountains
    mid_heights = []
    for x in range(WIDTH):
        nx = x / 150.0 
        h = NOISE.fractal2d(nx, 10.5, octaves=5, rigid=True)
        mid_heights.append(int(HEIGHT * 0.65 - (h * 110)))
        
    for x in range(WIDTH):
        y_start = mid_heights[x]
        for y in range(y_start, HEIGHT):
            if y < 0: continue
            
            # Mid-layer biological detail (Subtle blotches)
            # Domain Warping: Add turbulence to noise coordinates to break vertical striping
            warp_x = NOISE.fractal2d(x * 0.01, y * 0.01, octaves=1) * 40
            warp_y = NOISE.fractal2d(x * 0.01 + 100, y * 0.01, octaves=1) * 40

            nx = (x + warp_x) * 0.02
            ny = (y + warp_y) * 0.06
            bio_noise = NOISE.fractal2d(nx, ny + seed * 0.5, octaves=2)
            
            # Smooth color interpolation (lerp) to avoid sharp vertical edges
            mid_col = list(biome.mid_mount)
            if bio_noise > 0.6: # Treelines
                t = min(1.0, (bio_noise - 0.6) / 0.15)
                mid_col[0] = int(mid_col[0] * (1-t) + (mid_col[0]-20) * t)
                mid_col[1] = int(mid_col[1] * (1-t) + (mid_col[1]-10) * t)
                mid_col[2] = int(mid_col[2] * (1-t) + (mid_col[2]-20) * t)
            elif bio_noise < 0.4: # Fields/Sandbars
                t = min(1.0, (0.4 - bio_noise) / 0.15)
                mid_col[0] = int(mid_col[0] * (1-t) + (mid_col[0]+15) * t)
                mid_col[1] = int(mid_col[1] * (1-t) + (mid_col[1]+15) * t)
                mid_col[2] = int(mid_col[2] * (1-t) + (mid_col[2]+5) * t)

            # Mid layer: Medium haze (0.10)
            apply_shading(pixels, x, y, WIDTH, HEIGHT, seed, tuple(mid_col), strength=50.0, ns=0.04, haze=0.10, sky_color=biome.sky_bottom)
            
            # Sublte Rim Lighting on Mid mountain top edges
            if y == y_start:
                base = pixels[x, y]
                pixels[x, y] = color_clamp((base[0]+25, base[1]+25, base[2]+15))

    # 6. Foreground Terrain
    heights = []
    water_level = int(HEIGHT * 0.85)
    
    # COLLISION MASK for God Rays
    # 0 = Sky/Far (Pass through)
    # 1 = Mid (Soft Occlusion - Visible rays on top)
    # 2 = Fore (Hard Occlusion - Shadow)
    collision_mask = [[0 for _ in range(HEIGHT)] for _ in range(WIDTH)]
    
    for x in range(WIDTH):
        nx = x / 100.0
        h = NOISE.fractal2d(nx, 20.2, octaves=4)
        # Increased variance and shifted down to allow for deeper valleys (basins)
        y = int(HEIGHT * 0.85 + (h * 120 - 60)) 
        heights.append(y)

    for x in range(WIDTH):
        y_start = heights[x]
        
        # Liquids (Water/Lava)
        if y_start > water_level:
            # For lava, we often want it to look like it fills the entire basin to the bottom
            liquid_limit = HEIGHT if biome.liquid_type == 'lava' else min(y_start, HEIGHT)
            for wy in range(water_level, liquid_limit):
                 if biome.liquid_type == 'lava':
                     # OPAQUE LAVA
                     lc = biome.water_color
                     heat = NOISE.fractal2d(x * 0.1, (wy + seed*0.5) * 0.1, octaves=2)
                     glow = int(heat * 50)
                     pixels[x, wy] = color_clamp((lc[0] + glow, lc[1] + glow // 2, lc[2]))
                     if wy == water_level and random.random() < 0.12:
                         pixels[x, wy] = (255, 210, 80)
                 else:
                     # TRANSLUCENT WATER
                     wc = biome.water_color
                     dist = wy - water_level
                     ref_y = water_level - dist
                     ref_x = max(0, min(WIDTH-1, x + int(math.sin(wy * 0.2 + seed) * 2)))
                     if ref_y >= 0: bg = pixels[ref_x, ref_y]
                     else: bg = biome.sky_bottom
                     depth = (wy - water_level) / 20.0
                     w_alpha = min(0.85, 0.45 + depth)
                     nw = (int(wc[0]*w_alpha + bg[0]*(1-w_alpha)), int(wc[1]*w_alpha + bg[1]*(1-w_alpha)), int(wc[2]*w_alpha + bg[2]*(1-w_alpha)))
                     pixels[x, wy] = nw
                     if wy == water_level and random.random() < 0.15: pixels[x, wy] = (255, 255, 255)

        if y_start < HEIGHT:
            # FOREGROUND MASK (Hard)
            # Ensure indices are clamped
            for my in range(max(0, y_start), HEIGHT):
                collision_mask[x][my] = 2
                
            # Top with Rim Lighting
            for i in range(4):
                ty = y_start + i
                if ty >= 0 and ty < HEIGHT:
                    col = biome.ground_light
                    if i == 0: # Highlight the top-most pixel for depth separation
                        col = color_clamp((col[0] + 30, col[1] + 30, col[2] + 20))
                    pixels[x, ty] = col

            # [NEW] Enhanced Ground Cover and Overhanging Flora
            # Only draw if on solid ground (ABOVE or AT water level)
            if y_start <= water_level:
                local_r = random.Random(seed + x)
                # 1. Lush Ground Cover with Noise-Driven Density
                # Use a 1D noise pass to create "fertility" clusters
                fertility = NOISE.fractal2d(x * 0.05, seed * 0.1, octaves=2)
                base_richness = 0.8 if biome.liquid_type != 'lava' else 0.2
                # Modulate richness by fertility (range roughly 0.2 to 1.0)
                richness = base_richness * (0.3 + fertility * 0.7)
                
                if local_r.random() < richness:
                    draw_ground_cover(draw, x, y_start, biome, local_r)
                
                # 2. Overhanging Flora Detection
                # Check neighbors for cliffs
                is_cliff = False
                if x > 0 and (heights[x-1] - y_start) > 4: is_cliff = True
                if x < WIDTH-1 and (heights[x+1] - y_start) > 4: is_cliff = True
                
                if is_cliff and local_r.random() < 0.7:
                    draw_overhanging_flora(draw, x, y_start, biome, local_r)
                
                # 3. Wall Moss (Undergrowth)
                # Apply moss to vertical faces
                if x > 0 and (y_start - heights[x-1]) > 5:
                    # Left face is a cliff
                    for my in range(heights[x-1], y_start):
                        if local_r.random() < 0.15: # Random patches
                            draw_moss(pixels, x, my, local_r, biome.vine_color)
                if x < WIDTH-1 and (y_start - heights[x+1]) > 5:
                    # Right face is a cliff
                    for my in range(heights[x+1], y_start):
                        if local_r.random() < 0.15:
                            draw_moss(pixels, x, my, local_r, biome.vine_color)

            # Deep (Strata & MACRO ORES)
            for y in range(max(0, y_start + 4), HEIGHT):
                # ORES
                n_vein = NOISE.fractal2d(x * 0.02, y * 0.02, octaves=1)
                n_grain = NOISE.fractal2d(x * 0.2, y * 0.2, octaves=2)
                if n_vein > 0.65 and n_grain > 0.4:
                     pixels[x, y] = biome.accent
                     continue

                # STRATA
                depth = y - y_start
                # Noise warp for strata (wavy layers)
                # Low frequency noise for macro waves, higher for detail
                warp = NOISE.fractal2d(x * 0.03, y * 0.03, octaves=2) * 25.0
                effective_depth = depth + warp
                
                layer_height = 18
                layer_idx = int(effective_depth // layer_height) % len(biome.strata_colors)
                strata_col = biome.strata_colors[layer_idx]
                
                # Apply shading on top of strata for texture
                apply_shading(pixels, x, y, WIDTH, HEIGHT, seed+100, strata_col, strength=30.0, ns=0.08)

    # 6.6 Update masks for Mid mountains
    # SOFT Occlusion (1)
    # Only overwrite if 0 (don't overwrite Fore which is 2)
    for x in range(WIDTH):
        h_mid = NOISE.fractal2d(x / 150.0, 10.5, octaves=5, rigid=True)
        y_mid = int(HEIGHT * 0.65 - (h_mid * 110))
        for my in range(max(0, y_mid), HEIGHT): 
            if collision_mask[x][my] == 0:
                collision_mask[x][my] = 1

    # 7. STRUCTURES
    r_struct = random.Random(seed + 123)
    chunk_size = 50
    for chunk_x in range(0, WIDTH - chunk_size, chunk_size):
        if r_struct.random() < 0.2: 
            sx = chunk_x + chunk_size // 2
            sy = heights[sx]
            if sy > water_level: continue 
            stype = r_struct.choice(['monolith', 'lantern', 'alien_arch', 'multispire'])
            
            # Update mask with 2 (Hard Occlusion) for structures
            if stype == 'monolith':
                draw_monolith(pixels, sx, sy, r_struct.randint(0,999), biome)
                for mx in range(sx-7, sx+8):
                    if mx>=0 and mx<WIDTH:
                        for my in range(sy-100, sy):
                            if my>=0 and my<HEIGHT: collision_mask[mx][my] = 2
            elif stype == 'alien_arch':
                draw_alien_arch(pixels, sx, sy, r_struct.randint(0,999), biome)
                for mx in range(sx-40, sx+41):
                    if mx>=0 and mx<WIDTH:
                        for my in range(sy-120, sy):
                            if my>=0 and my<HEIGHT: collision_mask[mx][my] = 2
            elif stype == 'multispire':
                draw_multispire(pixels, sx, sy, r_struct.randint(0,999), biome)
                for mx in range(sx-28, sx+29):
                    if mx>=0 and mx<WIDTH:
                        for my in range(sy-130, sy):
                            if my>=0 and my<HEIGHT: collision_mask[mx][my] = 2
            elif stype == 'lantern':
                draw_lantern(pixels, sx, sy, r_struct.randint(0,999), biome)

    # 7.5 CONSOLIDATED LAVA GLOW (Post-Structures)
    if biome.liquid_type == 'lava':
        # Pre-calculate a blurred lava proximity map to avoid "pillars of light"
        lava_presence = [1.0 if heights[x] > water_level else 0.0 for x in range(WIDTH)]
        blurred_lava = [0.0] * WIDTH
        br = 35 # Blur radius
        
        # Simple box blur for proximity
        current_sum = sum(lava_presence[0:br])
        for x in range(WIDTH):
            # Slide window
            left = x - br
            right = x + br
            if left > 0:
                current_sum -= lava_presence[left-1]
            if right < WIDTH:
                current_sum += lava_presence[right]
            
            count = (min(WIDTH-1, right) - max(0, left) + 1)
            blurred_lava[x] = current_sum / count

        for x in range(WIDTH):
            lava_prox = blurred_lava[x]
            ground_top = heights[x]
            for y in range(HEIGHT):
                if collision_mask[x][y] > 0: # Terrain or structures
                    dist = abs(y - water_level)
                    
                    # Base ambient warmth
                    glow_alpha = 0.05
                    
                    if dist < 85:
                        # SURFACE PEAK (Pinned to water_level)
                        surface_peak = (1.0 - dist / 85.0) * 0.7
                        
                        # Intensity Noise
                        i_noise = NOISE.fractal2d(x * 0.08, y * 0.08, octaves=1)
                        surface_peak *= (0.5 + i_noise * 0.5)
                        
                        # HORIZONTAL DIFFUSION: Scale peak by our blurred map
                        # Maps [0, 1] proximity to [0.15, 1.0] multiplier
                        surface_peak *= (0.15 + lava_prox * 0.85)
                            
                        # Vertical Clipping
                        if y > ground_top + 3:
                            surface_peak = 0
                            
                        glow_alpha = max(glow_alpha, surface_peak)
                    
                    base = pixels[x, y]
                    pixels[x, y] = color_clamp((
                        int(base[0]*(1-glow_alpha) + 255*glow_alpha),
                        int(base[1]*(1-glow_alpha) + 110*glow_alpha),
                        int(base[2]*(1-glow_alpha) + 15*glow_alpha)
                    ))

    # 8. Vines & Trees
    tree_seed = seed + 900
    r_tree = random.Random(tree_seed)
    
    for x in range(1, WIDTH - 1):
        if x % 4 != 0: continue
        curr_h = heights[x]
        if curr_h > water_level: continue 
        if random.random() < 0.15:
            vh = random.randint(10, 35)
            for i in range(vh):
                # Add slight x-jitter for organic paths
                jitter = int(math.sin(i * 0.4 + seed) * 1.5)
                vx = max(0, min(WIDTH-1, x + jitter))
                vy = curr_h + 3 + i
                if vy < HEIGHT and vy < water_level:
                    pixels[vx, vy] = biome.vine_color
                    # Varied thickness near root
                    if i < vh // 4: 
                        if vx > 0: pixels[vx-1, vy] = biome.vine_color
                        if vx < WIDTH-1: pixels[vx+1, vy] = biome.vine_color

    for x in range(20, WIDTH - 20):
        if r_tree.random() < 0.02: 
            y = heights[x]
            if y < water_level:
                tree_h = r_tree.randint(20, 35)
                draw_tree(draw, x, y, tree_h/2, 0, 4, biome.accent, r_tree.randint(0,999), leaf_color=biome.vine_color)
                
                # Update Mask (Leaves = Hard Occlusion roughly)
                radius = int(tree_h/2)
                top_y = y - tree_h
                for tx in range(x-radius, x+radius):
                    for ty in range(max(0, top_y), y):
                         if tx>=0 and tx<WIDTH and ty>=0 and ty<HEIGHT:
                             if random.random() < 0.8: collision_mask[tx][ty] = 2

    # 9. LIGHTING ENGINE
    # Bloom Pass
    # We scan for "bright" pixels (runes, sun, stars) and bleed them
    # To save perf, we only blur a downscaled mask? 
    # Or just simple localized bloom for specific known emitters is faster.
    # We already did local glow for lanterns/sun.
    # Let's do a screen-space bloom for "Hot" pixels.
    
    # Identify hot pixels
    hot_pixels = []
    for y in range(0, HEIGHT, 2): 
        for x in range(0, WIDTH, 2):
            p = pixels[x, y]
            bri = (p[0] + p[1] + p[2]) / 3
            
            is_hot = False
            if bri > 230: is_hot = True
            elif biome.liquid_type == 'lava' and p[0] > 200 and p[1] < 150: # Lava signature
                is_hot = True
                
            if is_hot:
                hot_pixels.append((x, y, p))
    
    # Apply bloom
    for hx, hy, hc in hot_pixels:
        radius = 4
        for dy in range(-radius, radius+1):
            for dx in range(-radius, radius+1):
                px = hx + dx
                py = hy + dy
                if px < 0 or px >= WIDTH or py < 0 or py >= HEIGHT: continue
                
                dist = dx*dx + dy*dy
                if dist > radius*radius: continue
                
                factor = 0.2 * (1.0 - math.sqrt(dist)/radius)
                
                base = pixels[px, py]
                nr = min(255, int(base[0] + hc[0]*factor))
                ng = min(255, int(base[1] + hc[1]*factor))
                nb = min(255, int(base[2] + hc[2]*factor))
                pixels[px, py] = (nr, ng, nb)
                
    # God Rays (Sun Shafts)
    center_x = cx
    center_y = cy
    
    if celestial_visible and center_x > 0 and center_x < WIDTH:
        r_ray = random.Random(seed + 99)
        
        # Ray Color from Biome (Sync with celestial body)
        sc = biome.sun_color
        ray_col = (int(sc[0]*0.8 + 50), int(sc[1]*0.8 + 50), int(sc[2]*0.8 + 50))
        
        # Biome-specific intensity and ray count
        # Check sky brightness to determine if it's sunset/night
        sky_bri = (biome.sky_top[0] + biome.sky_top[1] + biome.sky_top[2]) / 3.0
        
        if sky_bri < 80:  # Very dark (night/corruption)
            ray_num = 30
            base_power = 0.25  # Much more visible rays
            ray_opacity_threshold = 0.1  # Draw rays 90% of the time
            ray_col = (int(ray_col[0]*0.7), int(ray_col[1]*0.7), int(ray_col[2]*0.7))
        elif sky_bri < 150:  # Sunset/twilight - MOST DRAMATIC
            ray_num = 35
            base_power = 0.30  # Very strong, solid rays
            ray_opacity_threshold = 0.05  # Draw rays 95% of the time for density
        else:  # Daytime
            ray_num = 20
            base_power = 0.08
            ray_opacity_threshold = 0.3  # Draw rays 70% of the time
        
        # If moon, adjust
        if biome.moon:
            ray_num = max(15, int(ray_num * 0.7))
            base_power *= 0.9  # Keep moon rays visible
            ray_opacity_threshold = 0.1
        
        for _ in range(ray_num):
            # WIDER angular spread - emanate in all downward directions
            angle = math.pi/2 + (r_ray.random() - 0.5) * 2.8  # ±1.4 radians = ~160 degree spread
            
            # VOLUMETRIC BEAM APPROACH
            # Instead of a thin raycast, we draw a WEDGE/CONE of light
            # Beam width increases with distance from sun
            
            max_distance = HEIGHT * 1.5
            step = 2  # Finer step for smoother beams
            
            for dist in range(0, int(max_distance), step):
                # Calculate centerline position
                center_x_ray = center_x + math.cos(angle) * dist
                center_y_ray = center_y + math.sin(angle) * dist
                
                # Beam width grows with distance (conical shape)
                beam_width = 2 + dist * 0.04  # Start wider, grow to ~60 pixels wide
                
                # Draw perpendicular slice across the beam
                perp_angle = angle + math.pi/2  # Perpendicular to ray direction
                
                for offset in range(int(-beam_width), int(beam_width) + 1):
                    # Calculate position across beam width
                    px = int(center_x_ray + math.cos(perp_angle) * offset)
                    py = int(center_y_ray + math.sin(perp_angle) * offset)
                    
                    if px < 0 or px >= WIDTH or py < 0 or py >= HEIGHT: continue
                    
                    # OCCLUSION CHECK
                    mask_val = collision_mask[px][py]
                    if mask_val == 2:  # Hard occlusion stops the entire beam
                        break
                    
                    # Distance falloff from sun
                    distance_power = base_power * (1.0 - dist/max_distance)
                    
                    # Proximity fade: reduce power very close to the sun to avoid point convergence
                    proximity_fade = min(1.0, dist / 100.0)  # Fade out in first 100 pixels
                    distance_power *= proximity_fade
                    
                    # Radial falloff across beam width (center is brightest)
                    radial_falloff = 1.0 - abs(offset) / beam_width if beam_width > 0 else 1.0
                    radial_falloff = radial_falloff ** 2  # Squared for softer edges
                    
                    power = distance_power * radial_falloff
                    
                    # Soft Occlusion (Mid)
                    if mask_val == 1:
                        power *= 0.5
                    
                    # Apply light
                    base = pixels[px, py]
                    nr = min(255, int(base[0] + ray_col[0]*power))
                    ng = min(255, int(base[1] + ray_col[1]*power))
                    nb = min(255, int(base[2] + ray_col[2]*power))
                    
                    # Less dithering for beams - we want them solid
                    if r_ray.random() > ray_opacity_threshold * 0.5:  # Even less dithering
                        pixels[px, py] = (nr, ng, nb)

    img = img.resize((WIDTH * SCALE, HEIGHT * SCALE), Image.NEAREST)
    img.save(output_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_landscape.py <output_path> [biome_name]")
        sys.exit(1)
    
    biome_arg = sys.argv[2] if len(sys.argv) > 2 else None
    generate_landscape(sys.argv[1], biome_arg)
