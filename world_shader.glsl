// Animated Pixel World - Ghostty Background Shader
// Emulates a pixel-art style procedural landscape with day/night cycle,
// drifting clouds, and wind.

// --- NOISE & HASH FUNCTIONS ---

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float noise(vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(p + vec2(0.0, 0.0));
    float b = hash(p + vec2(1.0, 0.0));
    float c = hash(p + vec2(0.0, 1.0));
    float d = hash(p + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

// Fractional Brownian Motion for clouds
float fbm(vec2 x) {
    float v = 0.0;
    float a = 0.5;
    vec2 shift = vec2(100.0);
    // Rotate to reduce axial bias
    mat2 rot = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.50));
    for (int i = 0; i < 4; ++i) {
        v += a * noise(x);
        x = rot * x * 2.0 + shift;
        a *= 0.5;
    }
    return v;
}

// --- MAIN RENDERER ---

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // Ghostty uses top-left origin for fragCoord.y, but Shadertoy math expects bottom-left.
    // Flip Y to fix upside-down rendering:
    vec2 fc = vec2(fragCoord.x, iResolution.y - fragCoord.y);

    // Pixelation Factor (Adjust this to change "pixel" size)
    float PIXEL_SIZE = 4.0;
    
    // Pixelated coordinates
    vec2 p = floor(fc / PIXEL_SIZE);
    vec2 res = floor(iResolution.xy / PIXEL_SIZE);
    vec2 uv = p / res; // Normalized pixelated coordinates (0 to 1)

    // Ensure aspect ratio is handled for coordinate-based math (e.g. circles)
    float aspect = res.x / res.y;
    vec2 p_norm = uv;
    p_norm.x *= aspect;

    // --- DAY/NIGHT CYCLE ---
    // Slow sine wave based on time: 0.0 = Night, 1.0 = Day
    float cycleSpeed = 0.02; // Slowed down significantly (approx 5 min per cycle)
    float cycle = (sin(iTime * cycleSpeed) + 1.0) * 0.5;

    // Day Palette
    vec3 d_skyTop = vec3(60., 140., 255.) / 255.0;
    vec3 d_skyBot = vec3(180., 220., 255.) / 255.0;
    vec3 d_farMt = vec3(100., 130., 160.) / 255.0;
    vec3 d_midMt = vec3(60., 90., 80.) / 255.0;
    vec3 d_ground = vec3(40., 120., 40.) / 255.0;
    vec3 d_sun = vec3(255., 255., 200.) / 255.0;
    vec3 d_cloud = vec3(1.0);

    // Night Palette
    vec3 n_skyTop = vec3(5., 5., 20.) / 255.0;
    vec3 n_skyBot = vec3(20., 10., 40.) / 255.0;
    vec3 n_farMt = vec3(20., 30., 50.) / 255.0;
    vec3 n_midMt = vec3(10., 20., 30.) / 255.0;
    vec3 n_ground = vec3(5., 15., 10.) / 255.0;
    vec3 n_sun = vec3(200., 220., 255.) / 255.0; // acts as moon
    vec3 n_cloud = vec3(0.3, 0.3, 0.4);

    // Sunset/Dawn Palette (Rich oranges, pinks, and purples)
    vec3 s_skyTop = vec3(100., 60., 140.) / 255.0;
    vec3 s_skyBot = vec3(255., 120., 60.) / 255.0;
    vec3 s_farMt = vec3(100., 50., 70.) / 255.0;
    vec3 s_midMt = vec3(60., 30., 45.) / 255.0;
    vec3 s_ground = vec3(35., 20., 25.) / 255.0;
    vec3 s_sun = vec3(255., 180., 100.) / 255.0;
    vec3 s_cloud = vec3(255., 160., 120.) / 255.0;

    // Interpolate Palette
    // cycle: 0.0 = Night, 0.5 = Sunset/Dawn, 1.0 = Day
    float w_night = smoothstep(0.5, 0.0, cycle);
    float w_day = smoothstep(0.5, 1.0, cycle);
    float w_sunset = 1.0 - w_night - w_day;

    vec3 cur_skyTop = n_skyTop * w_night + s_skyTop * w_sunset + d_skyTop * w_day;
    vec3 cur_skyBot = n_skyBot * w_night + s_skyBot * w_sunset + d_skyBot * w_day;
    vec3 cur_farMt = n_farMt * w_night + s_farMt * w_sunset + d_farMt * w_day;
    vec3 cur_midMt = n_midMt * w_night + s_midMt * w_sunset + d_midMt * w_day;
    vec3 cur_ground = n_ground * w_night + s_ground * w_sunset + d_ground * w_day;
    vec3 cur_sun = n_sun * w_night + s_sun * w_sunset + d_sun * w_day;
    vec3 cur_cloud = n_cloud * w_night + s_cloud * w_sunset + d_cloud * w_day;

    // --- DRAWING ---

    // 1. Sky Gradient
    vec3 col = mix(cur_skyBot, cur_skyTop, uv.y);

    // 1.5 Stars (Only visible at night)
    if (cycle < 0.5) {
        // Slowly rotate stars across the sky to match celestial movement
        float rotTime = iTime * cycleSpeed * 0.2; // Slow rotation
        float cr = cos(rotTime);
        float sr = sin(rotTime);
        mat2 rot = mat2(cr, -sr, sr, cr);
        
        // Rotate coordinates around center bottom
        vec2 starFc = fc - vec2(iResolution.x * 0.5, 0.0);
        starFc = rot * starFc;
        vec2 star_p = floor(starFc / PIXEL_SIZE);
        
        float starHash = hash(star_p);
        
        // Check original uv.y to keep stars above mountains
        if (starHash > 0.99 && uv.y > 0.3) {
            // Constant opacity (no blinking), fading out at dawn
            float starOpacity = clamp(1.0 - cycle * 2.0, 0.0, 1.0);
            col = mix(col, vec3(1.0), starOpacity);
        }
    }

    // 2. Celestial Body (Sun/Moon)
    float celestialY = 0.5 + sin(iTime * cycleSpeed) * 0.4; // Arcs across sky
    float celestialX = 0.5 + cos(iTime * cycleSpeed) * 0.4;
    vec2 celestialPos = vec2(celestialX * aspect, celestialY);
    
    if (distance(p_norm, celestialPos) < 0.05) {
        col = cur_sun;
    }

    // 3. Moving Clouds (in sky area only)
    if (uv.y > 0.3) {
        float cloudScale = 0.02;
        // Scroll over time
        float cloudNoise = fbm(vec2(p.x * cloudScale + iTime * 0.25, p.y * cloudScale * 2.0));
        if (cloudNoise > 0.6) {
            float cloudAlpha = smoothstep(0.6, 0.7, cloudNoise) * 0.8;
            col = mix(col, cur_cloud, cloudAlpha);
        }
    }

    // 4. Far Mountains
    float hFar = noise(vec2(p.x * 0.02, 0.0)) * 0.3 + 0.3;
    if (uv.y < hFar) {
        col = cur_farMt;
    }

    // 5. Mid Mountains
    float hMid = noise(vec2(p.x * 0.05, 12.34)) * 0.25 + 0.15;
    if (uv.y < hMid) {
        col = cur_midMt;
    }

    // 6. Ground Layer
    float hGround = noise(vec2(p.x * 0.1, 45.67)) * 0.1 + 0.08;
    if (uv.y < hGround) {
        col = cur_ground;
    }

    // 7. Wind Tufts (organic, wispy wind moving across the map)
    if (uv.y < 0.5 && uv.y > 0.05) {
        // Slowly drifting coordinate for organic noise shapes (stretched horizontally)
        vec2 windUv = vec2(p.x * 0.01 + iTime * 0.6, p.y * 0.05 + sin(p.x * 0.01 + iTime * 0.5)*0.02);
        float windNoise = fbm(windUv * 3.0);
        
        // Threshold heavily to only get isolated "tufts" of wind
        if (windNoise > 0.8) {
            // Secondary high-frequency noise to break tufts into dashed wisps (stretched)
            float wispBreak = noise(vec2(p.x * 0.04 + iTime * 0.75, p.y * 0.5 - iTime * 0.25));
            if (wispBreak > 0.4) {
                float windAlpha = smoothstep(0.65, 0.75, windNoise) * 0.4;
                vec3 windCol = mix(vec3(0.7, 0.7, 0.8), vec3(0.9, 0.95, 1.0), cycle);
                col = mix(col, windCol, windAlpha);
            }
        }
    }

    // 8. Fireflies (visible near the ground during dusk/night)
    float fireflyCycle = 1.0 - smoothstep(0.0, 0.6, cycle); 
    if (fireflyCycle > 0.0 && uv.y < hMid + 0.05) {
        // Create a 15x15 pixel grid to place one firefly per cell
        vec2 cellBase = floor(p / 15.0);
        vec3 fireflyTotal = vec3(0.0);
        
        // Check surrounding cells to allow fireflies to cross cell boundaries smoothly
        for(int y=-1; y<=1; y++) {
            for(int x=-1; x<=1; x++) {
                vec2 cellOffset = vec2(float(x), float(y));
                vec2 cell = cellBase + cellOffset;
                float f_hash = hash(cell);
                
                // Only 10% of cells have a firefly
                if (f_hash > 0.9) {
                    vec2 localP = (p / 15.0) - (cell + 0.5);
                    
                    // Wander around the cell center
                    float speed = 0.5 + f_hash;
                    float timeOff = f_hash * 100.0;
                    vec2 wander = vec2(
                        sin(iTime * speed + timeOff) * 0.4,
                        cos(iTime * speed * 1.1 + timeOff) * 0.4
                    );
                    
                    float dist = length(localP - wander);
                    
                    // Slow blinking twinkle
                    float twinkle = (sin(iTime * 2.0 + timeOff) + 1.0) * 0.5 * 0.8 + 0.2;
                    
                    // Sharp core and soft glow
                    float core = step(dist, 0.05); // The exact pixel
                    float glow = smoothstep(0.4, 0.0, dist) * 0.6;
                    
                    float intensity = (core + glow) * twinkle * fireflyCycle;
                    // Mix between yellow-green and golden-orange based on the firefly's hash
                    vec3 fireflyCol = mix(vec3(0.5, 1.0, 0.2), vec3(1.0, 0.8, 0.1), f_hash);
                    
                    fireflyTotal += fireflyCol * intensity;
                }
            }
        }
        // Additive blending for the glow
        col += fireflyTotal;
    }

    // --- Blend with Terminal Text ---
    // Ghostty passes the terminal text as iChannel0.
    vec2 termUv = fragCoord.xy / iResolution.xy;
    vec4 terminalColor = texture(iChannel0, termUv);
    
    // Since terminalColor.a is often 1.0 everywhere, we use a luminance key.
    // The Ghostty config sets the background to pure black (#000000), 
    // so anything brighter than near-black is terminal text.
    float luma = dot(terminalColor.rgb, vec3(0.299, 0.587, 0.114));
    float textMask = smoothstep(0.01, 0.05, luma);
    
    vec3 finalColor = mix(col, terminalColor.rgb, textMask);

    // --- Output ---
    fragColor = vec4(finalColor, 1.0);
}
