from config import Config

from whisperstream import WhisperStream

import json
import re

from input_handler import handle_input, expand_command, replace_number_words
import pyperclip

if __name__ == "__main__":
    cfg = Config("config.json")
    
    def callback(text):
        print(f"Obtained: {text}") 
        split_text = text.split()
        if split_text[0].lower() == cfg.dictate_prefix:
            copied_text = ' '.join(split_text[1:])
            capitalized = copied_text[0].upper() + copied_text[1:]
            print(f"Dictated: {capitalized}")
            pyperclip.copy(capitalized)
            print(f"Executing: {cfg.paste_shortcut}")
            handle_input(cfg.paste_shortcut, input_delay = cfg.input_delay)
            return

        command = ' '.join(split_text).lower().strip()
        clean_command = replace_number_words(re.sub(r'[?.!;:]', '', command))
        for pattern, response in cfg.commands.items():
            pattern_clean = re.sub(r'[?.!;:]', '', pattern.lower().strip())
    
            # Replace {numeric} with (\d+), {any} with (\S+)
            regex = re.escape(pattern_clean)
            regex = regex.replace(r"\{numeric\}", r"(\d+)")
            regex = regex.replace(r"\{any\}", r"(\S+)")  # matches any non-space string
            regex = "^" + regex + "$"
    
            match = re.fullmatch(regex, clean_command)
            if match:
                expanded_command = expand_command(response, match.groups())
                print(f"Executing: {expanded_command}")
                handle_input(expanded_command, input_delay = cfg.input_delay)
                break

    ws = WhisperStream(
            model_name = cfg.model_name,
            silence_seconds = cfg.silence_seconds,
            max_chunk_seconds = cfg.max_chunk_seconds,
            energy_threshold = cfg.energy_threshold,
            pre_roll_seconds = cfg.pre_roll_seconds,
            lang = cfg.lang,
            chunk_callback = callback
        )
    print(json.dumps(cfg.__dict__, indent=2))
    ws.start()
    input("Press Enter to stop\n")
    record = ws.end()
    #print(record)
