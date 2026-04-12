from .config import Config

from .whisperstream import WhisperStream
from .voskstream import VoskStream

import json
import re

from .input_handler import handle_input, handle_mouse_relative, expand_command, replace_number_words, char_map, append_script_path
import pyperclip

import sys

from .formatter import expand_numeric_placeholders

active_mode = None
previous_mode = None

from pathlib import Path

import warnings

from .abs_math import abs_add, abs_pow, abs_min

def main():
    global active_mode
    global previous_mode
    cfg = Config(Path.home() / ".config" / "libre-dictum")
    append_script_path(str(cfg.path))

    tray_enabled = False
    if cfg.enable_systray:
        from .systray import RGBTrayIcon
        tray = RGBTrayIcon("linux-voice-control")
        tray_enabled = True
   
    active_mode = cfg.starting_mode
    previous_mode = cfg.starting_mode
    print(active_mode)
    modes = {}

    def change_active_mode(mode_name):
        global active_mode
        global previous_mode
        if cfg.previous_mode_keyword == mode_name:
            mode_name = previous_mode
        if mode_name not in modes:
            warnings.warn(f"Mode not found: {mode_name}. Skipping...")
            return
        modes[active_mode].disable()
        if cfg.modes[active_mode]["exit_command"]:
            handle_input(cfg.modes[active_mode]["exit_command"], input_delay = cfg.modes[active_mode]["input_delay"], aliases = cfg.modes[active_mode]["aliases"], mode_change_callback = change_active_mode)
        previous_mode = active_mode
        active_mode = mode_name
        if tray_enabled:
            tray.set_mode(active_mode)
        if cfg.modes[active_mode]["enter_command"]:
            handle_input(cfg.modes[active_mode]["enter_command"], input_delay = cfg.modes[active_mode]["input_delay"], aliases = cfg.modes[active_mode]["aliases"], mode_change_callback = change_active_mode)
        modes[active_mode].enable()

    def mouse_callback_relative(dx, dy):
        if not cfg.modes[active_mode].get("ht_enabled"):
            return
        if dx == 0 and dy == 0:
            return
        if abs(dx) < cfg.modes[active_mode]["ht_dead_angle_h"]:
            dx = 0
        else:
            dx = abs_add(dx, -cfg.modes[active_mode]["ht_dead_angle_h"])
        if abs(dy) < cfg.modes[active_mode]["ht_dead_angle_v"]:
            dy = 0
        else:
            dy = abs_add(dy, -cfg.modes[active_mode]["ht_dead_angle_v"])
        
        if dx == 0 and dy == 0:
            return

        dx = abs_pow(dx, cfg.modes[active_mode]["ht_speed_power"]) * cfg.modes[active_mode]["ht_speed_mult"]
        dy = abs_pow(dy, cfg.modes[active_mode]["ht_speed_power"]) * cfg.modes[active_mode]["ht_speed_mult"]
        dx = abs_min(dx, cfg.modes[active_mode]["ht_max_speed"])
        dy = abs_min(dy, cfg.modes[active_mode]["ht_max_speed"])

        handle_mouse_relative(-dx, dy)

    def callback(text):
        global active_mode
        print(f"Obtained: {text}")
        split_text = text.split()
        command = ' '.join(split_text).strip()
        clean_command = replace_number_words(re.sub(r'[?.!;:]', '', command))
        command_lower = clean_command.lower()
        if command_lower == cfg.reload_command:
            cfg.reload()
            print("Config Reloaded")
            return
        if command_lower in modes:
            change_active_mode(command_lower)
            return
        if command_lower in cfg.modes[active_mode]["banned_strings"]:
            print(f"Skipping: '{text}' = '{command_lower}'")
            return
        for pattern, response in cfg.modes[active_mode]["commands"].items():
            pattern_clean = re.sub(r'[?.!;:]', '', pattern.lower().strip())
    
            # Replace {numeric} with (\d+), {any} with (\S+)
            regex = re.escape(pattern_clean)
            regex = regex.replace(r"\{numeric\}", r"(\d+)")
            regex = regex.replace(r"\{any\}", r"(\S+)")  # matches any non-space string
            regex = regex.replace(r"\{rest\}", r"(.+)")  # matches any string
            regex = "^" + regex + "$"
    
            match = re.fullmatch(regex, clean_command)
            if match:
                expanded_command = expand_command(response, match.groups())
                print(f"Executing: {expanded_command}")
                handle_input(expanded_command, input_delay = cfg.modes[active_mode]["input_delay"], aliases = cfg.modes[active_mode]["aliases"], mode_change_callback = change_active_mode)
                return
    for key, value in cfg.modes.items():
        if value["type"] == "vosk":
            modes[key] = VoskStream(
                    command_keys = expand_numeric_placeholders(list(value["commands"].keys())) + list(cfg.modes.keys()),
                    other_words = None,
                    model_path = value["path"],
                    chunk_callback = callback
                )
        elif value["type"] == "transformer":
            modes[key] = WhisperStream(
                    model_name = value["model_name"],
                    silence_seconds = value["silence_seconds"],
                    max_chunk_seconds = value["max_chunk_seconds"],
                    energy_threshold = value["energy_threshold"],
                    pre_roll_seconds = value["pre_roll_seconds"],
                    lang = value["lang"],
                    chunk_callback = callback
                )
        if tray_enabled:
            tray.add_mode(key, value["icon"])
    if cfg.enable_head_tracking:
        from .headtracking import FaceRotationTracker
        head_tracking = FaceRotationTracker(
                cfg.ht_model_path, 
                callback = mouse_callback_relative,
                camera_index = cfg.camera_index,
                min_detection_confidence = cfg.ht_min_detection_confidence,
                min_tracking_confidence = cfg.ht_min_tracking_confidence,
                offset_x = cfg.ht_offset_x,
                offset_y = cfg.ht_offset_y
            )
        head_tracking.start()

    #print(json.dumps(cfg.__dict__, indent=2))
    for mode in modes.values():
        mode.start()
    if active_mode:
        modes[active_mode].enable()
        if tray_enabled:
            tray.set_mode(active_mode)
            tray.show()

    input("Press Enter to stop\n")

if __name__ == "__main__":
    main()
