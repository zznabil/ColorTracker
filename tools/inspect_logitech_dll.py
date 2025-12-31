import ctypes
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def inspect_dll():
    dll_path = os.path.abspath("libs/ghub_device.dll")
    print(f"Loading DLL: {dll_path}")

    try:
        dll = ctypes.CDLL(dll_path)
        print("DLL Loaded Successfully!")

        # Check for common exports
        exports = ["logi_mouse_move", "move_relative", "mouse_event", "dl_move"]
        found = []
        for export in exports:
            if hasattr(dll, export):
                found.append(export)
                print(f"FOUND EXPORT: {export}")
            else:
                print(f"Missing: {export}")

        if found:
            print(f"\nSUCCESS: Engine can use {found[0]}")
            # Try to test call (dry run)
            try:
                print(f"Attempting dry-run call to {found[0]}(0,0)...")
                func = getattr(dll, found[0])
                # Most are (dx, dy) or (code, dx, dy).
                # We'll try generic catch
                func(0, 0)
                print("Call executed without crash.")
            except Exception as e:
                print(f"Call failed (expected if arguments wrong): {e}")
        else:
            print("\nFAILURE: No known exports found. This might be the wrong DLL version.")

    except Exception as e:
        print(f"Failed to load DLL: {e}")

if __name__ == "__main__":
    inspect_dll()
