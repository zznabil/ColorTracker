import timeit

import mss


def benchmark_mss():
    print("Initializing MSS Benchmark...")
    with mss.mss() as sct_default:
        with mss.mss(with_cursor=False) as sct_no_cursor:
            # Test cases: (width, height, label)
            test_cases = [
                (500, 500, "500x500"),
                (200, 200, "200x200 (Current)"),
                (120, 120, "120x120 (Proposed)"),
                (60, 60, "60x60 (Tight)"),
            ]

            print(f"{'Region':<25} | {'Cursor':<8} | {'Time/Frame':<12} | {'Max FPS':<10}")
            print("-" * 65)

            for w, h, label in test_cases:
                area = {"left": 0, "top": 0, "width": w, "height": h}

                # Test with cursor
                # Use default arg to bind current area value
                def grab_default(a=area):
                    return sct_default.grab(a)

                t1 = timeit.timeit(grab_default, number=100)
                avg_t1 = t1 / 100.0
                fps1 = 1.0 / avg_t1 if avg_t1 > 0 else 0
                print(f"{label:<25} | {'Yes':<8} | {avg_t1 * 1000:.2f} ms      | {fps1:.1f}")

                # Test without cursor
                # Use default arg to bind current area value
                def grab_no_cursor(a=area):
                    return sct_no_cursor.grab(a)

                t2 = timeit.timeit(grab_no_cursor, number=100)
                avg_t2 = t2 / 100.0
                fps2 = 1.0 / avg_t2 if avg_t2 > 0 else 0
                print(f"{label:<25} | {'No':<8} | {avg_t2 * 1000:.2f} ms      | {fps2:.1f}")
                print("-" * 65)


if __name__ == "__main__":
    benchmark_mss()
