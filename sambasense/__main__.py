"""SambaSense entry point — enables `python -m sambasense` and the `sambasense` console script."""

import sys


def main():
    """CLI entry point."""
    from sambasense.cli.commands import cli_main
    cli_main()


def main_gui():
    """GUI direct-launch entry point."""
    try:
        from sambasense.gui.app import run_app
        run_app()
    except ImportError as e:
        print(f"Error: GUI dependencies missing — {e}")
        print("Install PyQt6: pip install PyQt6")
        sys.exit(1)


if __name__ == "__main__":
    main()
