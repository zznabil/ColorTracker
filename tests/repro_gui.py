import traceback

import dearpygui.dearpygui as dpg


def log(msg):
    with open("repro_log.txt", "a") as f:
        f.write(str(msg) + "\n")


try:
    log("Starting DPG Context")
    dpg.create_context()

    class Config:
        def __init__(self):
            self.description = ""
            self.hotkey = ""

        def update(self, key, val):
            pass

    config = Config()

    log("Creating Window")
    with dpg.window(label="Test"):
        log("Creating Description Input")
        try:
            val = getattr(config, "description", "")
            log(f"Value: '{val}' Type: {type(val)}")
            dpg.add_input_text(
                label="Description",
                tag="meta_description",
                default_value=str(val),
                callback=lambda s, a: config.update("description", a),
            )
            log("Created Description input")
        except Exception:
            log(traceback.format_exc())

        log("Creating Hotkey Input")
        try:
            val = getattr(config, "hotkey", "")
            dpg.add_input_text(
                label="Hotkey",
                tag="meta_hotkey",
                default_value=str(val),
                callback=lambda s, a: config.update("hotkey", a),
                width=100,
            )
            log("Created Hotkey input")
        except Exception:
            log(traceback.format_exc())

    dpg.create_viewport(title="Custom Title", width=600, height=200)
    dpg.setup_dearpygui()
    log("DPG Setup Complete")
    # dpg.destroy_context()
    # Don't destroy immediately, maybe that causes issues?
    # But for headless test we must exit.
    log("Success")
except Exception as e:
    log(f"Global Fail: {e}")
    log(traceback.format_exc())
