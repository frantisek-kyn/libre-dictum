import json
import warnings

class Config:
    def __init__(self, path):
        self.path = path
        self.reload()

    def reload(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            warnings.warn(f"Configuration file '{self.path}' is missing. Using defaults.", UserWarning)
            data = {}
        self.reload_command = data.get("reload_command", "reload config")
        self.modes = data.get("modes", {})
        
        self.enable_systray = data.get("enable_systray", False)

        for mode in self.modes.values():
            mode_type = mode.get("type", None)
            mode.setdefault("icon", None)
            if not mode_type:
                raise Exception(f"Type of mode {mode.get('name')} is not set")
            mode.setdefault("commands", {})
            mode.setdefault("aliases", {})
            mode.setdefault("banned-strings", [])
            if mode_type == "transformer":
                mode.setdefault("model_name",  "whisper-turbo")
                mode.setdefault("silence_seconds",  0.3)
                mode.setdefault("max_chunk_seconds",  30.0)
                mode.setdefault("energy_threshold",  0.01)
                mode.setdefault("pre_roll_seconds",  0.25)
                mode.setdefault("lang",  "en")
                mode.setdefault("input_delay",  0.01)
                mode.setdefault("transformer_device",  "auto")
            elif mode_type == "vosk":
                path = mode.get("path", None)
                if not path:
                    raise Exception(f"Path of mode {mode.get('name')} is not set")
                mode.setdefault("input_delay",  0.01)
            else:
                raise Exception(f"Invalid mode type {mode_type}")
        
        self.starting_mode = data.get("starting_mode", list(self.modes.keys())[0] if len(self.modes) > 0 else None)
