"""Shared pytest fixtures for NimbusBill tests."""
import pytest
import sys
import os

# Add project root to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
