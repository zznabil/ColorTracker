import cv2
import numpy as np
import timeit

def benchmark_detection_methods():
    # 100x100 ROI (typical local search)
    img = np.random.randint(0, 256, (100, 100, 4), dtype=np.uint8)
    lower = np.array([100, 100, 100, 0], dtype=np.uint8)
    upper = np.array([150, 150, 150, 255], dtype=np.uint8)
    
    # Ensure at least one match
    img[50, 50] = [125, 125, 125, 255]
    
    mask = cv2.inRange(img, lower, upper)
    
    def method_minmax():
        _, max_val, _, max_loc = cv2.minMaxLoc(mask)
        return max_val > 0, max_loc
        
    def method_findnonzero():
        coords = cv2.findNonZero(mask)
        if coords is not None:
            return True, coords[0][0]
        return False, None

    t1 = timeit.timeit(method_minmax, number=10000)
    t2 = timeit.timeit(method_findnonzero, number=10000)
    
    print(f"minMaxLoc (10000 iterations): {t1:.4f}s")
    print(f"findNonZero (10000 iterations): {t2:.4f}s")

if __name__ == "__main__":
    benchmark_detection_methods()
