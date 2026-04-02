"""Tests for prollama CLI."""

import subprocess
import sys
from pathlib import Path

import pytest

from prollama import __version__


class TestCLI:
    """Test CLI functionality."""

    def test_version_output(self):
        """Test that CLI outputs correct version."""
        result = subprocess.run(
            [sys.executable, "-m", "prollama.cli", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert __version__ in result.stdout
        assert "prollama" in result.stdout.lower()

    def test_help_output(self):
        """Test that CLI help works."""
        result = subprocess.run(
            [sys.executable, "-m", "prollama.cli", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    def test_no_command_shows_help(self):
        """Test that running without command shows help."""
        result = subprocess.run(
            [sys.executable, "-m", "prollama.cli"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode != 0
        assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower()