import numpy as np
import cv2
import timeit

def benchmark_cv2_inrange():
    img = np.random.randint(0, 256, (500, 500, 4), dtype=np.uint8)
    lower4 = np.array([0, 0, 0, 0], dtype=np.uint8)
    upper4 = np.array([255, 255, 255, 255], dtype=np.uint8)
    
    lower3 = np.array([0, 0, 0], dtype=np.uint8)
    upper3 = np.array([255, 255, 255], dtype=np.uint8)
    
    def inrange_4ch():
        return cv2.inRange(img, lower4, upper4)
        
    def inrange_3ch():
        return cv2.inRange(img[:, :, :3], lower3, upper3)
        
    t1 = timeit.timeit(inrange_4ch, number=1000)
    t2 = timeit.timeit(inrange_3ch, number=1000)
    
    print(f"4-channel inRange (1000 iterations): {t1:.4f}s")
    print(f"3-channel inRange (1000 iterations): {t2:.4f}s")

if __name__ == "__main__":
    benchmark_cv2_inrange()
