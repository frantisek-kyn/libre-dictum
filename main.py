from config import Config

from whisperstream import WhisperStream

import json
import re

from input_handler import handle_input

if __name__ == "__main__":
    cfg = Config("config.json")
    
    def callback(text):
        splitted = text.split( )
        if splitted[0].lower() == cfg.command_prefix:
            command = ' '.join(splitted[1:]).lower().strip()
            clean_command = re.sub('[?.!;:]', "", command)
            if clean_command in cfg.commands:
                handle_input(cfg.commands[clean_command])

        print(text)

    
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
