"""Allows running the CLI with ``python -m robot_allocation``."""
from .cli.app import main

# `python -m robot_allocation` sets __name__ to "__main__" for this file,
# so `main()` only runs when the package is executed directly this way --
# not when it's merely imported by something else (e.g. by test code).
if __name__ == "__main__":
    main()
