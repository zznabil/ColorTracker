import ctypes
import timeit

def benchmark_ctypes_caching():
    # Simulate a user32 object
    class User32:
        def SendInput(self, a, b, c):
            return 1
            
    user32 = User32()
    
    def get_user32():
        # Simulate lookup overhead
        if hasattr(ctypes, "windll"):
            return user32
        return user32
        
    def call_lookup():
        u = get_user32()
        return u.SendInput(1, 2, 3)
        
    cached_send_input = user32.SendInput
    
    def call_cached():
        return cached_send_input(1, 2, 3)
        
    t1 = timeit.timeit(call_lookup, number=100000)
    t2 = timeit.timeit(call_cached, number=100000)
    
    print(f"Lookup (100k): {t1:.4f}s")
    print(f"Cached (100k): {t2:.4f}s")

if __name__ == "__main__":
    benchmark_ctypes_caching()
