"""
pytest configuration and shared fixtures for terminal-worlds tests.
"""
import sys
import os

# Ensure the project root is on sys.path so tests can import generate_landscape
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
