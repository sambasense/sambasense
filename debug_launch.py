
import sys
import os

print("Wrapper: Starting...")
sys.stdout.flush()

try:
    print("Wrapper: Importing run_app from sambasense.gui.app")
    from sambasense.gui.app import run_app
    print("Wrapper: calling run_app()")
    sys.stdout.flush()
    run_app()
    print("Wrapper: run_app() returned (unexpected)")
except Exception as e:
    print(f"Wrapper: Exception: {e}")
    import traceback
    traceback.print_exc()
except SystemExit as e:
    print(f"Wrapper: SystemExit: {e}")
finally:
    print("Wrapper: Exiting.")
