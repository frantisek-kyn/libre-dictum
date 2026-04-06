from config import Config

from whisperstream import WhisperStream
from voskstream import VoskStream

import json
import re

from input_handler import handle_input, expand_command, replace_number_words, char_map
import pyperclip

if __name__ == "__main__":
    cfg = Config("config.json")
   
    active_mode = cfg.starting_mode
    modes = {}
     
    def callback(text):
        print(f"Obtained: {text}")
        global active_mode
        split_text = text.split()
        command = ' '.join(split_text).lower().strip()
        clean_command = replace_number_words(re.sub(r'[?.!;:]', '', command))
        if clean_command == cfg.reload_command:
            cfg.reload()
            print("Config Reloaded")
        if clean_command in modes:
            modes[active_mode].disable()
            active_mode = clean_command
            modes[active_mode].enable()
            return
        for pattern, response in cfg.modes[active_mode]["commands"].items():
            pattern_clean = re.sub(r'[?.!;:]', '', pattern.lower().strip())
    
            # Replace {numeric} with (\d+), {any} with (\S+)
            regex = re.escape(pattern_clean)
            regex = regex.replace(r"\{numeric\}", r"(\d+)")
            regex = regex.replace(r"\{any\}", r"(\S+)")  # matches any non-space string
            regex = regex.replace(r"\{rest\}", r"(.+)")  # matches any non-space string
            regex = "^" + regex + "$"
    
            match = re.fullmatch(regex, clean_command)
            if match:
                expanded_command = expand_command(response, match.groups())
                print(f"Executing: {expanded_command}")
                handle_input(expanded_command, input_delay = cfg.modes[active_mode]["input_delay"])
                return
    for key, value in cfg.modes.items():
        if value["type"] == "vosk":
            modes[key] = VoskStream(
                    command_keys = list(value["commands"].keys()) + list(cfg.modes.keys()),
                    other_words = None,
                    model_path = value["path"], # Default Vosk local model directory
                    chunk_callback = callback
                )
        else:
            modes[key] = WhisperStream(
                    model_name = value["model_name"],
                    silence_seconds = value["silence_seconds"],
                    max_chunk_seconds = value["max_chunk_seconds"],
                    energy_threshold = value["energy_threshold"],
                    pre_roll_seconds = value["pre_roll_seconds"],
                    lang = value["lang"],
                    chunk_callback = callback
                )
    print(json.dumps(cfg.__dict__, indent=2))
    for mode in modes.values():
        mode.start()
    if active_mode:
        modes[active_mode].enable()

    input("Press Enter to stop\n")
    # record = ws.end()
    #print(record)
