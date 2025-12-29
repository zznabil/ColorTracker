import timeit

import mss


def benchmark_mss():
    with mss.mss() as sct_default:
        with mss.mss(with_cursor=False) as sct_no_cursor:
            area = {"left": 0, "top": 0, "width": 500, "height": 500}

            def grab_default():
                return sct_default.grab(area)

            def grab_no_cursor():
                return sct_no_cursor.grab(area)

            t1 = timeit.timeit(grab_default, number=100)
            t2 = timeit.timeit(grab_no_cursor, number=100)

            print(f"Default grab (100 iterations): {t1:.4f}s")
            print(f"No cursor grab (100 iterations): {t2:.4f}s")

if __name__ == "__main__":
    benchmark_mss()
