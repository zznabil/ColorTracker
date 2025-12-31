#!/usr/bin/env python3

"""
Main Window GUI

Sets up the main window GUI for the Color Tracking Algo for Single Player Games in Development application.
"""

import dearpygui.dearpygui as dpg


def setup_gui(app):
    """
    Set up the main window GUI with optimized real-time updates

    Args:
        app: The main application instance
    """

    def _apply_styling():
        with dpg.theme() as global_theme, dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (71, 71, 77), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Button, (91, 91, 102), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (111, 111, 122), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (201, 0, 141), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (201, 0, 141), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (231, 30, 171), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (201, 0, 141), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Header, (71, 71, 77), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (91, 91, 102), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (111, 111, 122), category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 6, 6, category=dpg.mvThemeCat_Core)
        dpg.bind_theme(global_theme)

    _apply_styling()

    # Create overlay for FOV display (prefer viewport drawlist to avoid blocking inputs)
    app.fov_overlay_enabled = False
    app._fov_use_viewport_drawlist = False
    screen_w = getattr(app.config, "screen_width", 1920)
    screen_h = getattr(app.config, "screen_height", 1440)

    try:
        # Viewport drawlist draws on the viewport and does not capture inputs
        app._fov_draw_surface = dpg.add_viewport_drawlist(front=True, tag="fov_viewport_drawlist")
        dpg.draw_rectangle(
            [0, 0],
            [100, 100],
            color=[0, 255, 0, 255],
            fill=[0, 255, 0, 30],
            thickness=2,
            tag="fov_rect",
            parent=app._fov_draw_surface,
            show=False,
        )
        app._fov_use_viewport_drawlist = True
    except Exception:
        # Fallback: window-based overlay (may block inputs in some DPG versions)
        with (
            dpg.window(
                label="FOV Overlay",
                width=screen_w,
                height=screen_h,
                no_title_bar=True,
                no_move=True,
                no_resize=True,
                no_collapse=True,
                no_background=True,
                no_bring_to_front_on_focus=True,
                no_inputs=True,
                show=False,
                tag="fov_overlay",
            ),
            dpg.drawlist(width=screen_w, height=screen_h, tag="fov_drawlist"),
        ):
            dpg.draw_rectangle(
                [0, 0],
                [100, 100],
                color=[0, 255, 0, 255],  # Bright green border
                fill=[0, 255, 0, 30],  # Semi-transparent green fill
                thickness=2,
                tag="fov_rect",
            )

    # Helper functions for FOV overlay with optimized updates
    def update_fov_overlay():
        try:
            if not app.fov_overlay_enabled:
                return

            fov_width = app.config.fov_x
            fov_height = app.config.fov_y
            # Use viewport size if drawing on viewport; otherwise use screen size from config
            if getattr(app, "_fov_use_viewport_drawlist", False):
                sw = dpg.get_viewport_width()
                sh = dpg.get_viewport_height()
            else:
                sw = getattr(app.config, "screen_width", 1920)
                sh = getattr(app.config, "screen_height", 1440)
            cx = int(sw // 2)
            cy = int(sh // 2)
            left = int(cx - (fov_width // 2))
            top = int(cy - (fov_height // 2))
            right = int(cx + (fov_width // 2))
            bottom = int(cy + (fov_height // 2))
            if dpg.does_item_exist("fov_rect"):
                dpg.configure_item("fov_rect", pmin=[left, top], pmax=[right, bottom])
        except Exception:
            # Fail silently to avoid breaking GUI
            pass

    def on_fov_overlay_toggled(sender, app_data):
        app.fov_overlay_enabled = bool(app_data)
        if app.fov_overlay_enabled:
            sw = getattr(app.config, "screen_width", 1920)
            sh = getattr(app.config, "screen_height", 1440)
            if getattr(app, "_fov_use_viewport_drawlist", False):
                # Show rectangle on viewport drawlist
                dpg.configure_item("fov_rect", show=True)
            else:
                if dpg.does_item_exist("fov_overlay"):
                    dpg.configure_item("fov_overlay", width=sw, height=sh)
                    dpg.set_item_pos("fov_overlay", [0, 0])
                    dpg.configure_item("fov_overlay", width=sw, height=sh)
                if dpg.does_item_exist("fov_drawlist"):
                    dpg.configure_item("fov_drawlist", width=sw, height=sh)
                # Make sure it doesn't block interactions
                dpg.configure_item("fov_overlay", no_inputs=True, no_bring_to_front_on_focus=True)
                dpg.show_item("fov_overlay")
            update_fov_overlay()
        elif getattr(app, "_fov_use_viewport_drawlist", False):
            dpg.configure_item("fov_rect", show=False)
        else:
            dpg.hide_item("fov_overlay")

    def on_fov_changed(sender, a, user_data):
        # Immediate value snapping with visual feedback
        snapped = max(5, min(250, round(a / 5) * 5))
        if abs(a - snapped) > 0.1:
            dpg.set_value(sender, snapped)
        app.config.update(user_data, snapped)
        if getattr(app, "fov_overlay_enabled", False):
            update_fov_overlay()

    def update_tolerance_preview():
        """Update the visual preview button to show the color tolerance range using direct color updates"""
        if not dpg.does_item_exist(app.tolerance_preview):
            return

        hex_color = app.config.target_color
        r, g, b = (hex_color >> 16) & 0xFF, (hex_color >> 8) & 0xFF, hex_color & 0xFF
        tol = app.config.color_tolerance

        # Update the tagged theme color items directly for performance and reliability
        # NOTE: DPG theme colors often expect normalized 0.0-1.0 floats or 0-255 ints depending on the item
        # To be safe and consistent with the picker, we use 0-255 ints for add_theme_color but ensure direct value updates
        if hasattr(app, "tolerance_color_item") and dpg.does_item_exist(app.tolerance_color_item):
            # VISUAL FIX: Apply tolerance to the normal state so feedback is immediate
            # We add the tolerance value to the base color to show the "expanded" range
            dpg.configure_item(
                app.tolerance_color_item,
                value=[min(255, r + tol), min(255, g + tol), min(255, b + tol), 255],
            )

        if hasattr(app, "tolerance_hover_item") and dpg.does_item_exist(app.tolerance_hover_item):
            # Show the "strictness" limit or highlighted state on hover
            # We use a multiplier to show a distinctly brighter version
            dpg.configure_item(
                app.tolerance_hover_item,
                value=[min(255, r + tol * 2.5), min(255, g + tol * 2.5), min(255, b + tol * 2.5), 255],
            )

    app.update_tolerance_preview = update_tolerance_preview

    def _create_styled_slider(label, default, min_val, max_val, callback, tooltip, user_data=None):
        with dpg.group(horizontal=True):
            dpg.add_text(label)
            slider = dpg.add_slider_float(
                label="",
                default_value=default,
                min_value=min_val,
                max_value=max_val,
                callback=callback,
                user_data=user_data,
                width=-1,
                format="%.3f" if isinstance(default, float) else "%d",
            )
            with dpg.tooltip(slider):
                dpg.add_text(tooltip)
        return slider

    def _create_styled_slider_int(label, default, min_val, max_val, callback, tooltip, user_data=None):
        with dpg.group(horizontal=True):
            dpg.add_text(label)
            slider = dpg.add_slider_int(
                label="",
                default_value=default,
                min_value=min_val,
                max_value=max_val,
                callback=callback,
                user_data=user_data,
                width=-1,
            )
            with dpg.tooltip(slider):
                dpg.add_text(tooltip)
        return slider

    def on_master_enable_changed(sender, app_data):
        """Update master enable state and sync UI visual feedback"""
        app.config.update("enabled", app_data)
        if dpg.does_item_exist("main_toggle_btn"):
            dpg.configure_item("main_toggle_btn", enabled=app_data)
            dpg.configure_item("main_toggle_btn", label="TOGGLE TRACKING" if app_data else "DISABLED (Master Off)")

    # Define reset function early to ensure it's available for modal callbacks
    def reset_all_settings():
        """Reset all settings to defaults and refresh the UI"""
        app.config.reset_to_defaults()
        if hasattr(app, "refresh_ui_from_config"):
            app.refresh_ui_from_config()
        dpg.hide_item("reset_confirmation_modal")
        if hasattr(app, "logger"):
            app.logger.info("Application settings reset to defaults.")

    app.reset_all_settings = reset_all_settings

    # Create main window with optimized layout
    with dpg.window(
        tag="main_window", label="Color Tracking Algo for Single Player Games in Development", width=480, height=730
    ):
        # --- PERSISTENT HEADER ---
        # A sleek, always-visible status bar
        with dpg.group(horizontal=True):
            dpg.add_text("STATUS:", color=(150, 150, 150))
            app.status_text = dpg.add_text("Idle", color=(255, 255, 255))
            dpg.add_spacer(width=20)
            dpg.add_text("FPS:", color=(150, 150, 150))
            app.fps_text = dpg.add_text("0.0", color=(255, 255, 255))

        dpg.add_spacer(height=5)

        # Master Toggle (Prominent)
        toggle_btn = dpg.add_button(
            label="ACTIVATE TRACKING",
            tag="main_toggle_btn",
            callback=lambda: app.toggle_algo(),
            width=-1,
            height=32,
        )
        with dpg.tooltip(toggle_btn):
            dpg.add_text("Master Switch: Click to Toggle Active/Idle State")

        dpg.add_spacer(height=10)
        dpg.add_separator()
        dpg.add_spacer(height=5)

        # Main Navigation Tabs
        with dpg.tab_bar():
            # ---------------------------
            # TAB 1: COMBAT (Logic & Physics)
            # ---------------------------
            with dpg.tab(label="  COMBAT  "):
                dpg.add_spacer(height=10)

                # SECTION: TARGETING PRIORITY
                dpg.add_text("TARGET PRIORITY", color=(201, 0, 141))
                with dpg.group(horizontal=True):
                    # Radio button group
                    aim_point_map = {0: "Head", 1: "Body", 2: "Legs"}
                    current_aim_point = aim_point_map.get(app.config.aim_point, "Body")

                    # We use a custom callback wrapper to map logic
                    def _on_aim_change(s, a):
                        app.config.update("aim_point", {"Head": 0, "Body": 1, "Legs": 2}.get(a, 1))

                    app.aim_point_radio = dpg.add_radio_button(
                        items=["Head", "Body", "Legs"],
                        default_value=current_aim_point,
                        horizontal=True,
                        callback=_on_aim_change,
                    )
                    with dpg.tooltip(app.aim_point_radio):
                        dpg.add_text("Prioritize where to aim on the target body.")

                dpg.add_spacer(height=10)

                # SECTION: OFFSETS (Micro-Adjustments)
                # Grouped with targeting because they directly affect WHERE we aim
                with dpg.collapsing_header(label="Precision Offsets", default_open=True):
                    _create_styled_slider_int(
                        "Head Offset (px)",
                        app.config.head_offset,
                        0,
                        100,
                        lambda s, a: app.config.update("head_offset", a),
                        "Vertical adjustment when aiming at HEAD.",
                    )
                    _create_styled_slider_int(
                        "Leg Offset (px)",
                        app.config.leg_offset,
                        0,
                        100,
                        lambda s, a: app.config.update("leg_offset", a),
                        "Vertical adjustment when aiming at LEGS.",
                    )

                dpg.add_spacer(height=15)
                dpg.add_separator()
                dpg.add_spacer(height=15)

                # SECTION: MOTION PHYSICS (1 Euro Filter)
                dpg.add_text("MOTION PHYSICS (1 Euro)", color=(201, 0, 141))

                # Stabilization
                dpg.add_text("Stabilization (Min Cutoff)")
                app.min_cutoff_slider = dpg.add_slider_float(
                    label="",
                    default_value=app.config.motion_min_cutoff,
                    min_value=0.01,
                    max_value=25.0,
                    callback=lambda s, a: [
                        dpg.set_value(s, round(a * 10) / 10),
                        app.config.update("motion_min_cutoff", round(a * 10) / 10),
                    ][-1],
                    width=-1,
                    format="%.1f",
                )
                with dpg.tooltip(app.min_cutoff_slider):
                    dpg.add_text("Low (0.1) = Heavy/Smooth. High (25.0) = Raw/Responsive.")

                dpg.add_spacer(height=5)

                # Responsiveness (Beta)
                dpg.add_text("Reflex Speed (Beta)")
                app.beta_slider = dpg.add_slider_float(
                    label="",
                    default_value=app.config.motion_beta,
                    min_value=0.0001,
                    max_value=0.3,
                    callback=lambda s, a: [
                        dpg.set_value(s, round(a * 1000) / 1000),
                        app.config.update("motion_beta", round(a * 1000) / 1000),
                    ][-1],
                    width=-1,
                    format="%.3f",
                )
                with dpg.tooltip(app.beta_slider):
                    dpg.add_text("Higher = Faster reaction to sudden direction changes.")

                dpg.add_spacer(height=5)

                # Prediction
                dpg.add_text("Velocity Prediction")
                app.prediction_scale_slider = dpg.add_slider_float(
                    label="",
                    default_value=app.config.prediction_scale,
                    min_value=0.0,
                    max_value=5.0,
                    callback=lambda s, a: app.config.update("prediction_scale", a),
                    width=-1,
                    format="%.2f x",
                )
                with dpg.tooltip(app.prediction_scale_slider):
                    dpg.add_text("Multiplies movement to lead the target.")

            # ---------------------------
            # TAB 2: VISION (Sensing)
            # ---------------------------
            with dpg.tab(label="  VISION  "):
                dpg.add_spacer(height=10)

                # SECTION: COLOR SENSE
                dpg.add_text("COLOR SPECTRUM", color=(201, 0, 141))

                # Hex Color handling
                hex_color = app.config.target_color
                init_r, init_g, init_b = (hex_color >> 16) & 0xFF, (hex_color >> 8) & 0xFF, hex_color & 0xFF

                # Helper to sync sliders
                def on_color_drag(sender, app_data):
                    # Update config
                    r = min(255, max(0, int(dpg.get_value(app.color_r))))
                    g = min(255, max(0, int(dpg.get_value(app.color_g))))
                    b = min(255, max(0, int(dpg.get_value(app.color_b))))
                    new_hex = (r << 16) | (g << 8) | b
                    app.config.update("target_color", new_hex)

                    # Update Display
                    if dpg.does_item_exist("theme_color_preview_val"):
                        dpg.configure_item("theme_color_preview_val", value=[r, g, b, 255])
                    app.update_tolerance_preview()  # Sync preview

                with dpg.group(horizontal=True):
                    # Color Sliders Column
                    with dpg.group(width=200):
                        app.color_r = dpg.add_slider_int(
                            label="R", default_value=init_r, max_value=255, callback=on_color_drag
                        )
                        with dpg.tooltip(app.color_r):
                            dpg.add_text("Red component (0-255).")
                        app.color_g = dpg.add_slider_int(
                            label="G", default_value=init_g, max_value=255, callback=on_color_drag
                        )
                        with dpg.tooltip(app.color_g):
                            dpg.add_text("Green component (0-255).")
                        app.color_b = dpg.add_slider_int(
                            label="B", default_value=init_b, max_value=255, callback=on_color_drag
                        )
                        with dpg.tooltip(app.color_b):
                            dpg.add_text("Blue component (0-255).")

                    # Preview Box Column
                    dpg.add_spacer(width=10)
                    with dpg.group():
                        dpg.add_text("Preview")
                        app.color_display_item = dpg.add_button(label="", width=60, height=60)
                        with dpg.theme() as theme_color_preview:
                            with dpg.theme_component(dpg.mvAll):
                                dpg.add_theme_color(
                                    dpg.mvThemeCol_Button, (init_r, init_g, init_b), tag="theme_color_preview_val"
                                )
                                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (init_r, init_g, init_b))
                                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (init_r, init_g, init_b))
                        dpg.bind_item_theme(app.color_display_item, theme_color_preview)
                        with dpg.tooltip(app.color_display_item):
                            dpg.add_text("Current target color preview.")

                dpg.add_spacer(height=10)

                # Tolerance
                dpg.add_text("Tolerance (Match Width)")
                app.tolerance_slider = dpg.add_slider_int(
                    label="",
                    default_value=app.config.color_tolerance,
                    max_value=100,
                    width=-1,
                    callback=lambda s, a: [app.config.update("color_tolerance", a), app.update_tolerance_preview()][-1],
                )
                with dpg.tooltip(app.tolerance_slider):
                    dpg.add_text("How 'strict' the color match is. Lower = Stricter.")

                # Tolerance Visualizer
                app.tolerance_preview = dpg.add_button(label="TOLERANCE VISUALIZER", width=-1, height=4)
                # (Theme for visualizer created dynamically in update_tolerance_preview)
                # Initialize visualizer theme
                with dpg.theme() as tol_theme:
                    with dpg.theme_component(dpg.mvAll):
                        app.tolerance_color_item = dpg.add_theme_color(
                            dpg.mvThemeCol_Button, (init_r, init_g, init_b), category=dpg.mvThemeCat_Core
                        )
                        app.tolerance_hover_item = dpg.add_theme_color(
                            dpg.mvThemeCol_ButtonHovered, (init_r, init_g, init_b), category=dpg.mvThemeCat_Core
                        )
                        dpg.add_theme_color(
                            dpg.mvThemeCol_ButtonActive, (init_r, init_g, init_b), category=dpg.mvThemeCat_Core
                        )
                dpg.bind_item_theme(app.tolerance_preview, tol_theme)
                with dpg.tooltip(app.tolerance_preview):
                    dpg.add_text("Visualizes the allowed color range.")

                dpg.add_spacer(height=15)
                dpg.add_separator()
                dpg.add_spacer(height=15)

                # SECTION: FIELD OF VIEW
                dpg.add_text("FIELD OF VIEW (FOV)", color=(201, 0, 141))

                with dpg.group(horizontal=True):
                    app.fov_x_slider = dpg.add_slider_int(
                        label="W",
                        default_value=app.config.fov_x,
                        min_value=5,
                        max_value=250,
                        width=140,
                        callback=on_fov_changed,
                        user_data="fov_x",
                    )
                    with dpg.tooltip(app.fov_x_slider):
                        dpg.add_text("Horizontal scan range in pixels.")
                    app.fov_y_slider = dpg.add_slider_int(
                        label="H",
                        default_value=app.config.fov_y,
                        min_value=5,
                        max_value=250,
                        width=140,
                        callback=on_fov_changed,
                        user_data="fov_y",
                    )
                    with dpg.tooltip(app.fov_y_slider):
                        dpg.add_text("Vertical scan range in pixels.")

                cb_overlay = dpg.add_checkbox(
                    label="Show Overlay (Green Box)", default_value=False, callback=on_fov_overlay_toggled
                )
                with dpg.tooltip(cb_overlay):
                    dpg.add_text("Draws a green box on screen showing the search area.")

                dpg.add_spacer(height=5)

            # ---------------------------
            # TAB 3: SYSTEM (Config & IO)
            # ---------------------------
            with dpg.tab(label="  SYSTEM  "):
                dpg.add_spacer(height=10)

                dpg.add_text("INPUT BINDINGS", color=(201, 0, 141))

                with dpg.group(horizontal=True):
                    dpg.add_text("START Key: ")
                    dpg.add_text(app.config.start_key.upper(), color=(0, 255, 0))

                with dpg.group(horizontal=True):
                    dpg.add_text("STOP Key:  ")
                    dpg.add_text(app.config.stop_key.upper(), color=(255, 0, 0))

                dpg.add_button(label="Rebind Keys (Config File Only)", width=-1, enabled=False)
                with dpg.tooltip(dpg.last_item()):
                    dpg.add_text("Edit config.json to change keys.")

                dpg.add_spacer(height=15)
                dpg.add_separator()
                dpg.add_spacer(height=15)

                dpg.add_text("PERFORMANCE", color=(201, 0, 141))

                _create_styled_slider_int(
                    "Target FPS Loop",
                    app.config.target_fps,
                    30,
                    1000,
                    lambda s, a: app.config.update("target_fps", a),
                    "Max cycles per second for the core thread.",
                )

                dpg.add_spacer(height=10)

                dpg.add_spacer(height=15)
                dpg.add_separator()
                dpg.add_spacer(height=15)

                dpg.add_text("DEBUGGING")
                dpg.add_checkbox(
                    label="Enable Debug Console",
                    default_value=app.config.debug_mode,
                    callback=lambda s, a: [
                        app.config.update("debug_mode", a),
                        app.logger.toggle_debug_console() if a else app.logger.hide_debug_console(),
                    ][-1],
                )
                with dpg.tooltip(dpg.last_item()):
                    dpg.add_text("Shows a separate window with internal logs.")

                dpg.add_spacer(height=20)
                dpg.add_separator()
                dpg.add_spacer(height=10)

                reset_btn = dpg.add_button(
                    label="RESET ALL SETTINGS",
                    callback=lambda: dpg.show_item("reset_confirmation_modal"),
                    width=-1,
                    height=30,
                )
                with dpg.theme() as reset_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (110, 40, 40), category=dpg.mvThemeCat_Core)
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (150, 50, 50), category=dpg.mvThemeCat_Core)
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (180, 60, 60), category=dpg.mvThemeCat_Core)
                dpg.bind_item_theme(reset_btn, reset_theme)
                with dpg.tooltip(reset_btn):
                    dpg.add_text("Warning: This will revert EVERY setting back to its factory default value.")

                def refresh_ui_from_config():
                    """Update all UI elements to match current config"""
                    ui_elements = [
                        (app.head_offset_slider, app.config.head_offset),
                        (app.leg_offset_slider, app.config.leg_offset),
                        (app.tolerance_slider, app.config.color_tolerance),
                        (app.fov_x_slider, app.config.fov_x),
                        (app.fov_y_slider, app.config.fov_y),
                        # (app.fps_slider, app.config.target_fps), # FPS slider callback might loop, safe to set?
                        (app.min_cutoff_slider, app.config.motion_min_cutoff),
                        (app.beta_slider, app.config.motion_beta),
                        (app.prediction_scale_slider, app.config.prediction_scale),
                    ]

                    for item, value in ui_elements:
                        if hasattr(app, "head_offset_slider") and dpg.does_item_exist(item):
                            dpg.set_value(item, value)

                    if dpg.does_item_exist(app.fps_slider):
                        dpg.set_value(app.fps_slider, app.config.target_fps)

                    if hasattr(app, "aim_point_radio") and dpg.does_item_exist(app.aim_point_radio):
                        dpg.set_value(
                            app.aim_point_radio, {0: "Head", 1: "Body", 2: "Legs"}.get(app.config.aim_point, "Body")
                        )

                    if hasattr(app, "color_r") and dpg.does_item_exist(app.color_r):
                        c = app.config.target_color
                        r, g, b = (c >> 16 & 0xFF), (c >> 8 & 0xFF), (c & 0xFF)
                        dpg.set_value(app.color_r, r)
                        dpg.set_value(app.color_g, g)
                        dpg.set_value(app.color_b, b)
                        if hasattr(app, "color_display_item") and dpg.does_item_exist("theme_color_preview_val"):
                            dpg.configure_item("theme_color_preview_val", value=[r, g, b, 255])

                    app.update_tolerance_preview()

                app.refresh_ui_from_config = refresh_ui_from_config
            # ---------------------------
            # TAB 4: STATS (Analytics)
            # ---------------------------
            with dpg.tab(label="  STATS  "):
                dpg.add_spacer(height=10)
                dpg.add_text("REAL-TIME ANALYTICS", color=(201, 0, 141))

                # Stats Summary
                with dpg.group(horizontal=True):
                    dpg.add_text("Current FPS:")
                    app.analytics_fps_val = dpg.add_text("0.0", color=(0, 255, 0))
                    dpg.add_spacer(width=20)
                    dpg.add_text("Avg Latency:")
                    app.analytics_latency_val = dpg.add_text("0.00ms", color=(0, 255, 255))

                with dpg.group(horizontal=True):
                    dpg.add_text("1% Low FPS:")
                    app.analytics_low_val = dpg.add_text("0.0", color=(255, 100, 100))
                    dpg.add_spacer(width=20)
                    dpg.add_text("Missed Frames:")
                    app.analytics_missed_val = dpg.add_text("0", color=(255, 50, 50))

                dpg.add_spacer(height=10)

                # FPS Graph
                dpg.add_text("FPS History (Last 1000 frames)")
                with dpg.plot(label="FPS", height=150, width=-1):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Time", no_tick_labels=True)
                    with dpg.plot_axis(dpg.mvYAxis, label="FPS"):
                        app.analytics_fps_series = dpg.add_line_series([], [], label="FPS")

                dpg.add_spacer(height=10)

                # Latency Graph
                dpg.add_text("Frame Latency (ms)")
                with dpg.plot(label="Latency", height=150, width=-1):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Time", no_tick_labels=True)
                    with dpg.plot_axis(dpg.mvYAxis, label="ms"):
                        app.analytics_latency_series = dpg.add_line_series([], [], label="Frame Time")
                        app.analytics_detection_series = dpg.add_line_series([], [], label="Detection Time")

                def update_analytics():
                    if not hasattr(app, "perf_monitor"):
                        return

                    stats = app.perf_monitor.get_stats()
                    history = app.perf_monitor.get_history()

                    # Update Text
                    dpg.set_value(app.analytics_fps_val, f"{stats['fps']:.1f}")
                    dpg.set_value(app.analytics_latency_val, f"{stats['avg_frame_ms']:.2f}ms")
                    dpg.set_value(app.analytics_low_val, f"{stats['one_percent_low_fps']:.1f}")
                    dpg.set_value(app.analytics_missed_val, f"{int(stats['missed_frames'])}")

                    # Update Graphs
                    if history["fps"]:
                        x_data = list(range(len(history["fps"])))
                        dpg.set_value(app.analytics_fps_series, [x_data, history["fps"]])

                    if history["frame_times"]:
                        x_data = list(range(len(history["frame_times"])))
                        dpg.set_value(app.analytics_latency_series, [x_data, history["frame_times"]])

                    if history["detection_times"]:
                        x_data = list(range(len(history["detection_times"])))
                        dpg.set_value(app.analytics_detection_series, [x_data, history["detection_times"]])

                app.update_analytics = update_analytics

            # ---------------------------
            # TAB 5: DEBUG (Rules)
            # ---------------------------
            # Only show if debug mode is effectively available or active
            # We'll just always show it but maybe disabled? No, let's just show it.
            with dpg.tab(label="  DEBUG  "):
                dpg.add_spacer(height=10)
                dpg.add_text("ADVANCED LOGGING", color=(201, 0, 141))
                dpg.add_text("Debug configuration is handled via config.json")

                # Debug rules visualizer removed per user feedback (non-functional)

        # Add update target status method to app with optimized status updates
        def update_target_status(found):
            if found:
                dpg.set_value(app.status_text, "Status: Target Locked")
                dpg.configure_item(app.status_text, color=(0, 255, 0))
            elif app.config.enabled:
                dpg.set_value(app.status_text, "Status: Scanning")
                dpg.configure_item(app.status_text, color=(255, 255, 0))
            else:
                dpg.set_value(app.status_text, "Status: Idle")
                dpg.configure_item(app.status_text, color=(255, 255, 255))

        app.update_target_status = update_target_status

        # Add FPS snap method to app
        def _snap_fps_value(value):
            """
            Snap FPS value to 120fps increments starting from 120fps

            Args:
                value: Raw slider value

            Returns:
                Snapped FPS value at 120fps intervals (120, 240, 360, 480, 600, 720, 840, 960)
            """
            # Calculate the snapped value by rounding to nearest 120fps increment
            snapped = max(120, round(value / 120) * 120)

            # Ensure we stay within bounds (120-960)
            return min(960, max(120, snapped))

        app._snap_fps_value = _snap_fps_value

    # --- MODALS ---
    with dpg.window(
        label="Confirm Reset",
        modal=True,
        show=False,
        tag="reset_confirmation_modal",
        no_title_bar=True,
        width=260,
        height=100,
        pos=[60, 200],
    ):
        dpg.add_spacer(height=5)
        dpg.add_text("Reset all settings to factory defaults?\nThis cannot be undone.", wrap=240)
        dpg.add_spacer(height=10)
        with dpg.group(horizontal=True):
            dpg.add_button(label="YES, RESET", callback=app.reset_all_settings, width=120, height=25)
            dpg.add_button(
                label="CANCEL", callback=lambda: dpg.hide_item("reset_confirmation_modal"), width=120, height=25
            )
