import math
import os
import random
import sys
import threading
import time

import dearpygui.dearpygui as dpg

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.detection import DetectionSystem
from core.motion_engine import MotionEngine
from utils.config import Config
from utils.performance_monitor import PerformanceMonitor


class RobustnessBenchmark:
    def __init__(self):
        self.config = Config()
        self.config.load()
        self.perf_monitor = PerformanceMonitor()

        # Override config for benchmark
        self.config.target_fps = 1000
        # Increase FOV to ensure target stays in view during large movements
        self.config.fov_x = 600
        self.config.fov_y = 600
        self.config.capture_method = "bettercam"  # Use ultra-speed if available
        self.config.target_color = 0x00FF00  # Green
        self.config.color_tolerance = 20

        try:
            self.detection = DetectionSystem(self.config, self.perf_monitor)
            # Access private method for benchmark info
            backend = self.detection._get_backend()
            print(f"[-] Backend: {backend.__class__.__name__}")
        except Exception as e:
            print(f"[!] Detection init failed: {e}")
            self.config.capture_method = "mss"
            self.detection = DetectionSystem(self.config, self.perf_monitor)

        self.motion = MotionEngine(self.config)

        self.running = False
        self.screen_w = 1920
        self.screen_h = 1080
        self.center_x = self.screen_w // 2
        self.center_y = self.screen_h // 2

        self.target_pos = [float(self.center_x), float(self.center_y)]
        self.cursor_pos = [float(self.center_x), float(self.center_y)]

        # Simulation parameters
        self.noise_intensity = 8.0  # High noise
        self.target_speed = 1.5
        self.loop_scale_x = 400
        self.loop_scale_y = 200

        # Metrics
        self.history_dist = []
        self.history_fps = []
        self.start_time = 0

    def _sim_loop(self):
        """
        Background loop to update simulation state
        """
        # Wait for GUI to start
        time.sleep(1.0)

        start_time = time.time()
        frames = 0

        while self.running:
            t_now = time.time()
            elapsed = t_now - start_time

            # 1. Move target in Figure-8 (Lemniscate)
            # x = a * cos(t) / (1 + sin^2(t))
            # y = a * sin(t) * cos(t) / (1 + sin^2(t))
            # Simplified parametric: x = sin(t), y = sin(t)cos(t)

            t = elapsed * self.target_speed
            denom = 1 + math.sin(t) ** 2
            self.target_pos[0] = self.center_x + (self.loop_scale_x * math.cos(t)) / denom
            self.target_pos[1] = self.center_y + (self.loop_scale_y * math.sin(t) * math.cos(t)) / denom

            # 2. Inject noise into cursor (Simulate hand jitter/recoil)
            # This pushes the cursor AWAY from the target, forcing the tracker to compensate
            noise_x = (random.random() - 0.5) * self.noise_intensity
            noise_y = (random.random() - 0.5) * self.noise_intensity
            self.cursor_pos[0] += noise_x
            self.cursor_pos[1] += noise_y

            # 3. Run Full Pipeline (Capture -> Detect -> Motion -> Move)
            # The 'cursor_pos' represents the center of the screen/fov in a game context?
            # Actually, in a 2D desktop sim, the 'cursor' is the mouse.
            # The 'DetectionSystem' captures the screen. It will see the Target at 'target_pos'.
            # 'find_target' returns the target's screen coordinates.

            try:
                # We need the DetectionSystem to actually SEE the green circle.
                # Since DPG draws it, DXGI/MSS will capture it.
                # Note: target_found will be True if visual rendering works.
                found, tx, ty = self.detection.find_target()

                if found:
                    # Motion Engine predicts where to move
                    # We pass the DETECTED coordinates (tx, ty)
                    # frame_time is 1/FPS (approx 1ms logic loop)
                    pred_x, pred_y = self.motion.process(tx, ty, 0.001)

                    # Apply movement to cursor
                    self.cursor_pos[0] = float(pred_x)
                    self.cursor_pos[1] = float(pred_y)

            except Exception:
                pass

            # 4. Calculate error (Euclidean distance)
            dist = math.sqrt(
                (self.cursor_pos[0] - self.target_pos[0]) ** 2 + (self.cursor_pos[1] - self.target_pos[1]) ** 2
            )
            self.history_dist.append(dist)
            frames += 1

            # Limit loop speed to target_fps (1000Hz) logic
            # Use busy wait for precision in benchmark
            while time.time() - t_now < 0.001:
                pass

        avg_fps = frames / (time.time() - start_time)
        print(f"[-] Sim Loop Finished. Avg Logic FPS: {avg_fps:.1f}")

    def run_gui(self):
        dpg.create_context()
        dpg.create_viewport(title="Tracking Robustness Benchmark (Phase 6)", width=1920, height=1080)
        dpg.setup_dearpygui()
        # dpg.toggle_viewport_fullscreen()

        # Use explicit tag for the window
        with dpg.window(
            label="Overlay",
            tag="benchmark_window",
            width=1920,
            height=1080,
            no_title_bar=True,
            no_move=True,
            no_resize=True,
            no_background=True,
        ):
            dpg.add_draw_layer(tag="overlay_layer")

        self.running = True
        t = threading.Thread(target=self._sim_loop, daemon=True)
        t.start()

        dpg.show_viewport()
        dpg.set_primary_window("benchmark_window", True)

        # Run for 10 seconds then exit (User requirement)
        start_time = time.time()

        while dpg.is_dearpygui_running():
            if time.time() - start_time > 10.0:
                break

            dpg.delete_item("overlay_layer", children_only=True)

            # Draw Target (Green Circle) - The thing we track
            dpg.draw_circle(
                center=(int(self.target_pos[0]), int(self.target_pos[1])),
                radius=15,
                color=(0, 255, 0, 255),
                fill=(0, 255, 0, 255),
                parent="overlay_layer",
            )

            # Draw Simulated Cursor (Red Cross) - The thing moving
            cx, cy = int(self.cursor_pos[0]), int(self.cursor_pos[1])
            dpg.draw_line((cx - 20, cy), (cx + 20, cy), color=(255, 0, 0, 255), thickness=3, parent="overlay_layer")
            dpg.draw_line((cx, cy - 20), (cx, cy + 20), color=(255, 0, 0, 255), thickness=3, parent="overlay_layer")

            # Stats
            if len(self.history_dist) > 0:
                avg_err = sum(self.history_dist[-100:]) / min(len(self.history_dist), 100)
                dpg.draw_text(
                    (50, 50),
                    f"Tracking Error: {avg_err:.2f} px",
                    size=30,
                    color=(255, 255, 255, 255),
                    parent="overlay_layer",
                )
                dpg.draw_text(
                    (50, 90),
                    "Simulating: 8.0 Noise Intensity + Figure-8 Path",
                    size=20,
                    color=(200, 200, 200, 255),
                    parent="overlay_layer",
                )

            dpg.render_dearpygui_frame()

        self.running = False
        dpg.destroy_context()
        self.detection.close()

        # Final Report
        if len(self.history_dist) > 0:
            avg = sum(self.history_dist) / len(self.history_dist)
            print("\n=== BENCHMARK RESULTS ===")
            print(f"Average Tracking Error: {avg:.2f} pixels")
            print(f"Samples: {len(self.history_dist)}")
            print("=========================")


if __name__ == "__main__":
    bench = RobustnessBenchmark()
    bench.run_gui()
