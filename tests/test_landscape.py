"""
Test suite for terminal-worlds landscape generator.

Design principles (from CLAUDE.md):
- Use fixed seeds for all noise tests — no flakiness from randomness
- Pass tmp_path for output files — no filesystem pollution
- Treat the render pipeline as a black box; test inputs/outputs not internals
- Full suite must complete in under 60 seconds
"""
import pytest
from PIL import Image

from generate_landscape import SmoothNoise, Palette, BIOMES, generate_landscape, WIDTH, HEIGHT, SCALE


# ---------------------------------------------------------------------------
# SmoothNoise
# ---------------------------------------------------------------------------

class TestSmoothNoise:
    def test_noise2d_range(self):
        """noise2d must return values in [0, 1]."""
        n = SmoothNoise(seed=42)
        for xi in range(20):
            for yi in range(20):
                v = n.noise2d(xi * 0.1, yi * 0.1)
                assert 0.0 <= v <= 1.0, f"noise2d({xi*0.1}, {yi*0.1}) = {v} out of range"

    def test_noise2d_deterministic(self):
        """Same seed must produce identical output."""
        n1 = SmoothNoise(seed=7)
        n2 = SmoothNoise(seed=7)
        for xi in range(10):
            for yi in range(10):
                assert n1.noise2d(xi * 0.3, yi * 0.3) == n2.noise2d(xi * 0.3, yi * 0.3)

    def test_noise2d_seed_variation(self):
        """Different seeds must not produce identical outputs."""
        n1 = SmoothNoise(seed=1)
        n2 = SmoothNoise(seed=9999)
        samples_differ = any(
            n1.noise2d(x * 0.17, y * 0.13) != n2.noise2d(x * 0.17, y * 0.13)
            for x in range(5) for y in range(5)
        )
        assert samples_differ, "Different seeds produced identical noise — check hash function"

    def test_fractal2d_range(self):
        """fractal2d must return values in [0, 1]."""
        n = SmoothNoise(seed=123)
        for xi in range(15):
            for yi in range(15):
                v = n.fractal2d(xi * 0.05, yi * 0.05, octaves=4, persistence=0.5)
                assert 0.0 <= v <= 1.0, f"fractal2d out of range: {v}"

    def test_fractal2d_rigid_range(self):
        """fractal2d with rigid=True must also return values in [0, 1]."""
        n = SmoothNoise(seed=77)
        for xi in range(10):
            for yi in range(10):
                v = n.fractal2d(xi * 0.1, yi * 0.1, octaves=3, persistence=0.5, rigid=True)
                assert 0.0 <= v <= 1.0, f"fractal2d rigid out of range: {v}"

    def test_fractal2d_deterministic(self):
        """fractal2d is deterministic for the same seed and inputs."""
        n1 = SmoothNoise(seed=55)
        n2 = SmoothNoise(seed=55)
        for xi in range(8):
            assert n1.fractal2d(xi * 0.2, 0.5) == n2.fractal2d(xi * 0.2, 0.5)


# ---------------------------------------------------------------------------
# Palette / BIOMES
# ---------------------------------------------------------------------------

class TestPalette:
    REQUIRED_ATTRS = [
        "name", "sky_top", "sky_bottom", "far_mount", "mid_mount",
        "ground_dark", "ground_light", "accent", "cloud_color", "vine_color",
        "water_color", "sun_color", "moon", "structure_base", "rune_color",
        "strata_colors", "liquid_type",
    ]

    def test_all_four_biomes_present(self):
        names = {b.name for b in BIOMES}
        assert names == {"forest", "desert", "corruption", "volcanic"}

    @pytest.mark.parametrize("biome_name", ["forest", "desert", "corruption", "volcanic"])
    def test_biome_has_required_attributes(self, biome_name):
        biome = next(b for b in BIOMES if b.name == biome_name)
        for attr in self.REQUIRED_ATTRS:
            assert hasattr(biome, attr), f"Biome '{biome_name}' missing attribute '{attr}'"

    @pytest.mark.parametrize("biome_name", ["forest", "desert", "corruption", "volcanic"])
    def test_color_tuples_are_valid_rgb(self, biome_name):
        """All RGB color tuples must be 3-element tuples of ints 0–255."""
        biome = next(b for b in BIOMES if b.name == biome_name)
        color_attrs = [
            "sky_top", "sky_bottom", "far_mount", "mid_mount", "ground_dark",
            "ground_light", "accent", "cloud_color", "vine_color", "water_color",
            "sun_color", "structure_base", "rune_color",
        ]
        for attr in color_attrs:
            color = getattr(biome, attr)
            assert len(color) == 3, f"{biome_name}.{attr} is not a 3-tuple"
            for channel in color:
                assert 0 <= channel <= 255, f"{biome_name}.{attr} channel {channel} out of range"

    @pytest.mark.parametrize("biome_name", ["forest", "desert", "corruption", "volcanic"])
    def test_strata_colors_valid(self, biome_name):
        biome = next(b for b in BIOMES if b.name == biome_name)
        assert len(biome.strata_colors) >= 1, f"{biome_name} has no strata_colors"
        for color in biome.strata_colors:
            assert len(color) == 3

    def test_liquid_types(self):
        """Forest and desert should use 'water'; volcanic should use 'lava'."""
        by_name = {b.name: b for b in BIOMES}
        assert by_name["forest"].liquid_type == "water"
        assert by_name["volcanic"].liquid_type == "lava"


# ---------------------------------------------------------------------------
# generate_landscape — smoke tests
# ---------------------------------------------------------------------------

class TestGenerateLandscape:
    """
    End-to-end smoke tests. These are the slowest tests (~5s per biome).
    They verify the pipeline does not crash and produces a valid PNG at the
    correct output resolution.
    """

    @pytest.mark.parametrize("biome_name", ["forest", "desert", "corruption", "volcanic"])
    def test_biome_generates_valid_png(self, tmp_path, biome_name):
        """Each biome must produce a 1920×1080 PNG without exceptions."""
        output = tmp_path / f"{biome_name}.png"
        generate_landscape(str(output), biome_name)

        assert output.exists(), f"Output file not created for biome '{biome_name}'"

        img = Image.open(str(output))
        expected_w = WIDTH * SCALE
        expected_h = HEIGHT * SCALE
        assert img.size == (expected_w, expected_h), (
            f"Expected {expected_w}×{expected_h}, got {img.size} for biome '{biome_name}'"
        )
        assert img.mode == "RGB", f"Expected RGB mode, got {img.mode}"

    def test_unknown_biome_falls_back_to_random(self, tmp_path):
        """An unrecognised biome name should not raise — it falls back to random."""
        output = tmp_path / "fallback.png"
        # Should not raise
        generate_landscape(str(output), "nonexistent_biome")
        assert output.exists()

    def test_no_biome_arg_generates_random(self, tmp_path):
        """Calling with biome_name=None should produce a valid image."""
        output = tmp_path / "random.png"
        generate_landscape(str(output), None)
        assert output.exists()
        img = Image.open(str(output))
        assert img.size == (WIDTH * SCALE, HEIGHT * SCALE)
