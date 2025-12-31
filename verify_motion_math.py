class OneEuroFilterSim:
    def __init__(self, min_cutoff, beta):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = 1.0
        self.value_prev = 0.0
        self.deriv_prev = 0.0

    def predict_cutoff(self, dt, dx_val):
        # Simulate derivative calculation
        # Minimize simulation logic for lint compliance
        # t_e = dt

        # r_d = 2 * math.pi * self.d_cutoff * t_e
        # a_d = r_d / (r_d + 1)

        # dx is speed (px/sec)
        dx = dx_val  # already in units/sec

        # Simple smoothing for derivative simulation
        dx_hat = dx  # Assume steady state for simplicity

        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        return cutoff


def simulate():
    print("--- 1 Euro Filter Cutoff Simulation ---")
    print("Scenario: 1px jitter at 240 FPS (dt = 0.00416s)")
    dt = 1 / 240
    pixel_move = 1.0  # 1 pixel jitter
    speed = pixel_move / dt  # 240 px/sec
    print(f"Effective Speed (dx/dt): {speed:.2f} px/sec")

    betas = [0.01, 0.1, 1.0, 5.0, 25.0]
    min_cutoffs = [1.0, 5.0, 10.0, 25.0]

    print(f"{'Beta':<10} | {'Min Cutoff':<10} | {'Resulting Cutoff (Hz)':<20} | {'Effect'}")
    print("-" * 65)

    for beta in betas:
        for mc in min_cutoffs:
            sim = OneEuroFilterSim(mc, beta)
            cutoff = sim.predict_cutoff(dt, speed)

            effect = "Filtering"
            if cutoff > 120:  # Nyquist of 240Hz
                effect = "PASS-THROUGH (No Smoothing)"
            elif cutoff > 60:
                effect = "Light Smoothing"
            elif cutoff < 1:
                effect = "Heavy Lag"

            print(f"{beta:<10} | {mc:<10} | {cutoff:<20.4f} | {effect}")


if __name__ == "__main__":
    simulate()
