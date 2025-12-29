import numpy as np
import timeit
import mss

def benchmark_buffer_conversion():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        
        raw_bytes = sct_img.bgra
        h, w = sct_img.height, sct_img.width
        
        def current_method():
            return np.frombuffer(raw_bytes, dtype=np.uint8).reshape((h, w, 4))
            
        def verify_zero_copy():
            arr = current_method()
            # Check if it shares memory with the source (raw_bytes is bytes, which is immutable, 
            # so frombuffer creates a view but the data is copied if we try to write to it? 
            # No, frombuffer on bytes returns a read-only array).
            return arr.flags.owndata == False
            
        print(f"Zero Copy Verified: {verify_zero_copy()}")
        
        # Benchmark
        t = timeit.timeit(current_method, number=10000)
        print(f"Current method (frombuffer + reshape) 10000 iterations: {t:.4f}s")
        print(f"Avg time per iteration: {t/10000*1000:.6f} ms")

if __name__ == "__main__":
    benchmark_buffer_conversion()
