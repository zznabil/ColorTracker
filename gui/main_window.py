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
    # Set up theme with immediate visual feedback
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
        # Add immediate visual feedback for interactive elements
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 6, 6, category=dpg.mvThemeCat_Core)

    dpg.bind_theme(global_theme)

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

    def on_fov_x_changed(sender, a):
        # Immediate value snapping with visual feedback
        snapped = max(25, min(250, round(a / 25) * 25))
        if abs(a - snapped) > 0.1:  # Only update if value changed significantly
            dpg.set_value(sender, snapped)
        app.config.update("fov_x", snapped)
        if getattr(app, "fov_overlay_enabled", False):
            update_fov_overlay()

    def on_fov_y_changed(sender, a):
        # Immediate value snapping with visual feedback
        snapped = max(25, min(250, round(a / 25) * 25))
        if abs(a - snapped) > 0.1:  # Only update if value changed significantly
            dpg.set_value(sender, snapped)
        app.config.update("fov_y", snapped)
        if getattr(app, "fov_overlay_enabled", False):
            update_fov_overlay()

    def on_master_enable_changed(sender, app_data):
        """Update master enable state and sync UI visual feedback"""
        app.config.update("enabled", app_data)
        if dpg.does_item_exist("main_toggle_btn"):
            dpg.configure_item("main_toggle_btn", enabled=app_data)
            dpg.configure_item("main_toggle_btn", label="TOGGLE TRACKING" if app_data else "DISABLED (Master Off)")

    # Create main window with optimized layout
    with dpg.window(
        tag="main_window", label="Color Tracking Algo for Single Player Games in Development", width=380, height=520
    ):
        # Header section - Always visible
        dpg.add_text("COLOR TRACKER V3", color=(201, 0, 141))

        with dpg.group(horizontal=True):
            app.status_text = dpg.add_text("Status: Idle")
            app.fps_text = dpg.add_text("FPS: 0.0")

        dpg.add_separator()

        # Main Navigation
        with dpg.tab_bar():
            # --- HOME TAB ---
            with dpg.tab(label="Home"):
                dpg.add_spacer(height=5)

                # Active Control Group
                with dpg.group(horizontal=True):
                    toggle_btn = dpg.add_button(
                        label="TOGGLE TRACKING",
                        tag="main_toggle_btn",
                        callback=lambda: app.toggle_algo(),
                        width=180,
                        height=30,
                    )
                    with dpg.tooltip(toggle_btn):
                        dpg.add_text("The main On/Off switch. Click this to start or stop the bot.")

                    app.enabled_checkbox = dpg.add_checkbox(
                        label="Master Enable",
                        default_value=app.config.enabled,
                        callback=on_master_enable_changed,
                    )
                    with dpg.tooltip(app.enabled_checkbox):
                        dpg.add_text("The 'Safety' switch. If this is OFF, the hotkeys won't work.")

                    # Initial state sync
                    if not app.config.enabled:
                        dpg.configure_item("main_toggle_btn", enabled=False, label="DISABLED (Master Off)")

                dpg.add_spacer(height=10)
                dpg.add_separator()
                dpg.add_spacer(height=10)

                # Core Sensitivity
                dpg.add_text("AIM SMOOTHING (Hand Steadiness)", color=(201, 0, 141))
                app.smoothing_slider = dpg.add_slider_float(
                    label="",
                    default_value=app.config.smoothing,
                    min_value=0.0,
                    max_value=50.0,
                    callback=lambda s, a: [
                        snapped := max(0.0, min(50.0, round(a / 0.5) * 0.5)),
                        dpg.set_value(s, snapped),
                        app.config.update("smoothing", snapped),
                    ][-1],
                    clamped=True,
                    format="%.1f",
                    width=-1,
                )
                with dpg.tooltip(app.smoothing_slider):
                    dpg.add_text("High = slow and steady (sniper style), Low = fast and twitchy (pro-flicker style).")

                dpg.add_spacer(height=20)
                dpg.add_text("HOTKEYS:", color=(150, 150, 150))
                dpg.add_text(f"  {app.config.start_key.upper()}: Start Tracking")
                dpg.add_text(f"  {app.config.stop_key.upper()}: Stop Tracking")
                if hasattr(app.config, "debug_mode") and app.config.debug_mode:
                    dpg.add_text("  F12: Toggle Console")

            # --- AIM TAB ---
            with dpg.tab(label="Aim"):
                dpg.add_spacer(height=5)

                dpg.add_text("TARGETING SETTINGS", color=(201, 0, 141))
                with dpg.group(horizontal=True):
                    dpg.add_text("Aim At:")
                    aim_point_map = {0: "Head", 1: "Body", 2: "Legs"}
                    current_aim_point = aim_point_map.get(app.config.aim_point, "Body")
                    app.aim_point_radio = dpg.add_radio_button(
                        items=["Head", "Body", "Legs"],
                        default_value=current_aim_point,
                        horizontal=True,
                        callback=lambda s, a: app.config.update(
                            "aim_point", {"Head": 0, "Body": 1, "Legs": 2}.get(a, 1)
                        ),
                    )
                    with dpg.tooltip(app.aim_point_radio):
                        dpg.add_text("Where to shoot: Like picking between a headshot or a body shot.")

                dpg.add_spacer(height=10)
                dpg.add_text("FILTER BRAIN (Smoothing Logic):")
                app.filter_combo = dpg.add_combo(
                    items=["EMA", "DEMA", "TEMA", "Median+EMA", "Dynamic EMA"],
                    default_value=app.config.filter_method,
                    callback=lambda s, a: app.config.update("filter_method", a),
                    width=-1,
                )
                with dpg.tooltip(app.filter_combo):
                    dpg.add_text("EMA is standard, TEMA/DEMA are 'High-Speed' versions with less lag.")

                dpg.add_spacer(height=10)
                dpg.add_separator()
                dpg.add_spacer(height=10)

                dpg.add_text("MICRO-ADJUSTMENTS (Offsets)", color=(201, 0, 141))

                with dpg.group(horizontal=True):
                    dpg.add_text("Head:")
                    app.head_offset_slider = dpg.add_slider_int(
                        label="",
                        default_value=app.config.head_offset,
                        min_value=0,
                        max_value=100,
                        callback=lambda s, a: [dpg.set_value(s, a), app.config.update("head_offset", a)][-1],
                        width=-1,
                    )
                    with dpg.tooltip(app.head_offset_slider):
                        dpg.add_text("Nudge the aim up: Micro-adjust higher to hit the top of the head.")

                with dpg.group(horizontal=True):
                    dpg.add_text("Legs:")
                    app.leg_offset_slider = dpg.add_slider_int(
                        label="",
                        default_value=app.config.leg_offset,
                        min_value=0,
                        max_value=100,
                        callback=lambda s, a: [dpg.set_value(s, a), app.config.update("leg_offset", a)][-1],
                        width=-1,
                    )
                    with dpg.tooltip(app.leg_offset_slider):
                        dpg.add_text("Nudge the aim down: Micro-adjust lower to hit the boots.")

            # --- DETECTION TAB ---
            with dpg.tab(label="Detection"):
                dpg.add_spacer(height=5)

                dpg.add_text("COLOR SENSING", color=(201, 0, 141))
                with dpg.group(horizontal=True):
                    dpg.add_text("Target Color: ")

                    # Convert hex color to RGB
                    hex_color = app.config.target_color
                    r = (hex_color >> 16) & 0xFF
                    g = (hex_color >> 8) & 0xFF
                    b = hex_color & 0xFF

                    # Function to update tolerance preview color
                    def update_tolerance_preview():
                        hex_color = app.config.target_color
                        target_r = (hex_color >> 16) & 0xFF
                        target_g = (hex_color >> 8) & 0xFF
                        target_b = hex_color & 0xFF
                        tolerance = app.config.color_tolerance
                        if tolerance == 0:
                            preview_r, preview_g, preview_b = target_r, target_g, target_b
                        else:
                            brightness_factor = tolerance * 2.5
                            preview_r = min(255, target_r + brightness_factor)
                            preview_g = min(255, target_g + brightness_factor)
                            preview_b = min(255, target_b + brightness_factor)

                        if hasattr(app, "tolerance_preview") and hasattr(app, "tolerance_theme"):
                            dpg.delete_item(app.tolerance_theme)
                            with dpg.theme() as new_tolerance_theme:
                                with dpg.theme_component(dpg.mvButton):
                                    dpg.add_theme_color(
                                        dpg.mvThemeCol_Button,
                                        [preview_r, preview_g, preview_b, 255],
                                        category=dpg.mvThemeCat_Core,
                                    )
                                    dpg.add_theme_color(
                                        dpg.mvThemeCol_ButtonHovered,
                                        [preview_r, preview_g, preview_b, 255],
                                        category=dpg.mvThemeCat_Core,
                                    )
                                    dpg.add_theme_color(
                                        dpg.mvThemeCol_ButtonActive,
                                        [preview_r, preview_g, preview_b, 255],
                                        category=dpg.mvThemeCat_Core,
                                    )
                            app.tolerance_theme = new_tolerance_theme
                            dpg.bind_item_theme(app.tolerance_preview, new_tolerance_theme)

                            tooltip_text = f"Tolerance: {tolerance}\nRange: ±{tolerance * 2.5:.1f} brightness"
                            tooltip_tag = f"{app.tolerance_preview}_tooltip"
                            if dpg.does_item_exist(tooltip_tag):
                                dpg.delete_item(tooltip_tag)
                            with dpg.tooltip(app.tolerance_preview, tag=tooltip_tag):
                                dpg.add_text(tooltip_text)

                    app.update_tolerance_preview = update_tolerance_preview

                    app.color_picker = dpg.add_color_edit(
                        label="",
                        default_value=[r, g, b],
                        callback=lambda s, a: [
                            app.config.update(
                                "target_color", (int(a[0] * 255) << 16) | (int(a[1] * 255) << 8) | int(a[2] * 255)
                            ),
                            app.update_tolerance_preview(),
                        ][-1],
                        no_alpha=True,
                        width=100,
                    )
                    with dpg.tooltip(app.color_picker):
                        dpg.add_text("Pick the color you want to track.")

                dpg.add_spacer(height=5)
                dpg.add_text("Color Tolerance (Strictness):")
                with dpg.group(horizontal=True):
                    app.tolerance_slider = dpg.add_slider_int(
                        label="",
                        default_value=app.config.color_tolerance,
                        min_value=0,
                        max_value=50,
                        width=250,
                        callback=lambda s, a: [
                            snapped := max(0, min(50, round(a / 5) * 5)),
                            dpg.set_value(s, snapped),
                            app.config.update("color_tolerance", snapped),
                            update_tolerance_preview(),
                        ][-1],
                    )
                    app.tolerance_preview = dpg.add_button(label="", width=40, height=20)
                    with dpg.theme() as tolerance_theme, dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, [r, g, b, 255], category=dpg.mvThemeCat_Core)
                    app.tolerance_theme = tolerance_theme
                    dpg.bind_item_theme(app.tolerance_preview, tolerance_theme)
                app.update_tolerance_preview()

                dpg.add_spacer(height=10)
                dpg.add_separator()
                dpg.add_spacer(height=10)

                dpg.add_text("SEARCH AREA (FOV)", color=(201, 0, 141))
                with dpg.group(horizontal=True):
                    dpg.add_text("Width:")
                    app.fov_x_slider = dpg.add_slider_int(
                        label="",
                        default_value=app.config.fov_x,
                        min_value=25,
                        max_value=250,
                        callback=on_fov_x_changed,
                        width=-1,
                    )
                    with dpg.tooltip(app.fov_x_slider):
                        dpg.add_text("Horizontal scan range (pixels). Smaller is faster but requires better aim.")

                with dpg.group(horizontal=True):
                    dpg.add_text("Height:")
                    app.fov_y_slider = dpg.add_slider_int(
                        label="",
                        default_value=app.config.fov_y,
                        min_value=25,
                        max_value=250,
                        callback=on_fov_y_changed,
                        width=-1,
                    )
                    with dpg.tooltip(app.fov_y_slider):
                        dpg.add_text("Vertical scan range (pixels). Keep tight to avoid distractions.")

                app.fov_overlay_checkbox = dpg.add_checkbox(
                    label="Show Visual Search Box (Overlay)", default_value=False, callback=on_fov_overlay_toggled
                )
                with dpg.tooltip(app.fov_overlay_checkbox):
                    dpg.add_text("Draws a green box showing exactly where the bot is looking.")

            # --- SYSTEM TAB ---
            with dpg.tab(label="System"):
                dpg.add_spacer(height=5)

                dpg.add_text("PROFILES", color=(201, 0, 141))

                """
                def refresh_profile_combo():
                    # Disabled
                    pass

                def update_metadata_fields():
                    # Disabled
                    pass

                def on_profile_selected(sender, app_data):
                    # Disabled
                    pass
                """

                def refresh_ui_from_config():
                    """Update all UI elements to match current config"""
                    ui_elements = [
                        (app.smoothing_slider, app.config.smoothing),
                        (app.filter_combo, app.config.filter_method),
                        (app.head_offset_slider, app.config.head_offset),
                        (app.leg_offset_slider, app.config.leg_offset),
                        (app.tolerance_slider, app.config.color_tolerance),
                        (app.fov_x_slider, app.config.fov_x),
                        (app.fov_y_slider, app.config.fov_y),
                        (app.fps_slider, app.config.target_fps),
                        (app.prediction_checkbox, app.config.prediction_enabled),
                        (app.prediction_slider, app.config.prediction_multiplier),
                        (app.enabled_checkbox, app.config.enabled),
                    ]

                    for item, value in ui_elements:
                        if dpg.does_item_exist(item):
                            dpg.set_value(item, value)

                    if dpg.does_item_exist(app.aim_point_radio):
                        dpg.set_value(
                            app.aim_point_radio, {0: "Head", 1: "Body", 2: "Legs"}.get(app.config.aim_point, "Body")
                        )

                    if dpg.does_item_exist(app.color_picker):
                        c = app.config.target_color
                        dpg.set_value(
                            app.color_picker, [(c >> 16 & 0xFF) / 255.0, (c >> 8 & 0xFF) / 255.0, (c & 0xFF) / 255.0]
                        )

                    app.update_tolerance_preview()

                """
                dpg.add_combo(
                    items=app.config.list_profiles(),
                    default_value=app.config.current_profile_name,
                    tag="profile_combo",
                    callback=on_profile_selected,
                    width=-1,
                )

                dpg.add_spacer(height=5)
                dpg.add_text("Metadata:")
                try:
                    dpg.add_input_text(label="Description", tag="meta_description")
                    dpg.set_value("meta_description", str(getattr(app.config, "description", "")))
                    dpg.set_item_callback("meta_description", lambda s, a: app.config.update("description", a))
                except Exception as e:
                    print(f"Warning: Failed to init description input: {e}")

                try:
                    dpg.add_input_text(label="Hotkey", tag="meta_hotkey", width=100)
                    dpg.set_value("meta_hotkey", str(getattr(app.config, "hotkey", "")))
                    dpg.set_item_callback("meta_hotkey", lambda s, a: app.config.update("hotkey", a))
                except Exception as e:
                    print(f"Warning: Failed to init hotkey input: {e}")
                with dpg.tooltip("meta_hotkey"):
                    dpg.add_text("Example: F1, Ctrl+P. (Visual reference only currently)")

                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Save As...",
                        callback=lambda: dpg.show_item("save_profile_modal"),
                        width=80,
                    )
                    dpg.add_button(
                        label="Rename",
                        callback=lambda: dpg.show_item("rename_profile_modal"),
                        width=80,
                    )
                    dpg.add_button(
                        label="Duplicate",
                        callback=lambda: dpg.show_item("duplicate_profile_modal"),
                        width=80,
                    )
                    dpg.add_button(
                        label="Delete",
                        callback=lambda: dpg.show_item("delete_profile_modal"),
                        width=80,
                    )
                """

                dpg.add_spacer(height=10)
                dpg.add_separator()
                dpg.add_spacer(height=10)

                dpg.add_text("PERFORMANCE", color=(201, 0, 141))
                dpg.add_text("Target Update Rate (FPS):")
                app.fps_slider = dpg.add_slider_int(
                    label="",
                    default_value=app.config.target_fps,
                    min_value=120,
                    max_value=960,
                    callback=lambda s, a: [
                        snapped := app._snap_fps_value(a),
                        dpg.set_value(s, snapped),
                        app.config.update("target_fps", snapped),
                    ][-1],
                    width=-1,
                )
                with dpg.tooltip(app.fps_slider):
                    dpg.add_text("Higher = smoother aim but more CPU usage. Use 240/360 for best results.")

                dpg.add_spacer(height=10)
                dpg.add_separator()
                dpg.add_spacer(height=10)

                dpg.add_text("PREDICTION (Anti-Lag)", color=(201, 0, 141))
                app.prediction_checkbox = dpg.add_checkbox(
                    label="Enable Predictive Leading",
                    default_value=app.config.prediction_enabled,
                    callback=lambda s, a: app.config.update("prediction_enabled", a),
                )

                with dpg.group(horizontal=True):
                    dpg.add_text("Strength:")
                    app.prediction_slider = dpg.add_slider_float(
                        label="",
                        default_value=app.config.prediction_multiplier,
                        min_value=0.1,
                        max_value=50.0,
                        callback=lambda s, a: [
                            snapped := max(0.1, min(50.0, round(a / 0.5) * 0.5)),
                            dpg.set_value(s, snapped),
                            app.config.update("prediction_multiplier", snapped),
                        ][-1],
                        width=-1,
                        format="%.1f",
                    )
                with dpg.tooltip(app.prediction_slider):
                    dpg.add_text("Strength: Higher = aims further in front of the runner.")

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

            # --- DEBUG TAB (Conditional) ---
            if hasattr(app, "logger") and app.logger.debug_console_enabled:
                with dpg.tab(label="Debug"):
                    dpg.add_spacer(height=5)
                    dpg.add_button(
                        label="Toggle Debug Console (F12)",
                        callback=lambda: app.toggle_debug_console() if hasattr(app, "toggle_debug_console") else None,
                        width=-1,
                    )

                    dpg.add_spacer(height=10)
                    dpg.add_text("Debug Filters:", color=(201, 0, 141))

                    debug_rules = [
                        ("performance_monitoring", "Perf Stats"),
                        ("target_detection_events", "Detection"),
                        ("system_state_changes", "System State"),
                        ("mouse_movement_events", "Movement"),
                        ("configuration_changes", "Config"),
                        ("error_tracking", "Errors"),
                        ("gui_events", "GUI"),
                        ("keyboard_events", "Hotkeys"),
                    ]

                    app.debug_rule_checkboxes = {}
                    for rule_key, rule_name in debug_rules:
                        cb = dpg.add_checkbox(
                            label=rule_name,
                            default_value=app.logger.debug_rules.get(rule_key, False),
                            callback=lambda s, a, rule=rule_key: app.logger.toggle_debug_rule(rule, a),
                        )
                        app.debug_rule_checkboxes[rule_key] = cb
                        with dpg.tooltip(cb):
                            dpg.add_text(f"Enable or disable recursive debug logging for {rule_name.lower()}.")

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

        def reset_all_settings():
            """Reset all settings to defaults and refresh the UI"""
            app.config.reset_to_defaults()
            refresh_ui_from_config()
            dpg.hide_item("reset_confirmation_modal")
            if hasattr(app, "logger"):
                app.logger.info("Application settings reset to defaults.")

        app.reset_all_settings = reset_all_settings

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

    """
    # Save Profile Modal
    def save_new_profile(sender, app_data):
        # Disabled
        pass

    # ... Modal windows commented out ...
    """
