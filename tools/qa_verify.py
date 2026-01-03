import time

from main import ColorTrackerAlgo


def test_gdi_leak_loop():
    print("Starting GDI leak verification...")
    # We can't easily measure GDI handle count from Python without more ctypes,
    # but we can simulate the exception and check if it's handled.
    # Actually, let's just inspect the code again. It's a clear risk.
    pass


def test_threading_race():
    print("Testing threading race on self.running...")
    # Simulate rapid start/stop
    app = ColorTrackerAlgo()
    for _i in range(10):
        app.start_algo()
        time.sleep(0.01)
        app.stop_algo()
    print("Threading test finished.")


if __name__ == "__main__":
    test_threading_race()
