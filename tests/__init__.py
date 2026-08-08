"""Ensures ``src/`` is importable without requiring an editable install.

python -m unittest discover imports this package first, so inserting the
src path here makes ``import robot_allocation...`` work from any test
module without every file needing its own sys.path hack.
"""
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
