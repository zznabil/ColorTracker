import ctypes
import time

import mss


def debug_pixel_color():
    with mss.mss() as sct:
        print("Move your mouse over a known color (e.g., RED or YELLOW).")
        print("Press Ctrl+C to stop.")

        try:
            while True:
                # Get cursor position
                class POINT(ctypes.Structure):
                    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
                pt = POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))

                # Capture 1x1 pixel
                monitor = {"top": pt.y, "left": pt.x, "width": 1, "height": 1}
                sct_img = sct.grab(monitor)

                # Method A: .pixel(0, 0) - Supposedly RGB
                pixel_val = sct_img.pixel(0, 0)

                # Method B: Raw bytes - Supposedly BGRA
                raw_bytes = sct_img.bgra

                # Print both
                print(f"Pos: ({pt.x}, {pt.y}) | .pixel(): {pixel_val} (RGB?) | Raw Bytes: {list(raw_bytes)} (BGRA?)", end='\r')
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nStopped.")

if __name__ == "__main__":
    debug_pixel_color()
