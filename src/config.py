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
            mode.setdefault("type", "import")
            mode.setdefault("icon", None)
            mode.setdefault("commands", {})
            mode.setdefault("aliases", {})
            mode.setdefault("banned_strings", [])
            for imported_mode in [self.modes[key] for key in mode.get("imports", []) if key in self.modes]:
                if "model_name" in imported_mode:
                    mode.setdefault("model_name", imported_mode["model_name"])
                if "silence_seconds" in imported_mode:
                    mode.setdefault("silence_seconds", imported_mode["silence_seconds"])
                if "max_chunk_seconds" in imported_mode:
                    mode.setdefault("max_chunk_seconds", imported_mode["max_chunk_seconds"])
                if "energy_threshold" in imported_mode:
                    mode.setdefault("energy_threshold", imported_mode["energy_threshold"])
                if "pre_roll_seconds" in imported_mode:
                    mode.setdefault("pre_roll_seconds", imported_mode["pre_roll_seconds"])
                if "lang" in imported_mode:
                    mode.setdefault("lang", imported_mode["lang"])
                if "input_delay" in imported_mode:
                    mode.setdefault("input_delay", imported_mode["input_delay"])
                if "transformer_device" in imported_mode:
                    mode.setdefault("transformer_device", imported_mode["transformer_device"])
                if "path" in imported_mode:
                    mode.setdefault("path", imported_mode["path"])
                if "input_delay" in imported_mode:
                    mode.setdefault("input_delay", imported_mode["input_delay"])
                mode["commands"] = imported_mode.get("commands", {}) | mode["commands"]
                mode["aliases"] = imported_mode.get("aliases", {}) | mode["aliases"]
                mode["banned_strings"].extend(imported_mode.get("banned_strings", []))

            if mode["type"] == "transformer":
                mode.setdefault("model_name",  "whisper-turbo")
                mode.setdefault("silence_seconds",  0.3)
                mode.setdefault("max_chunk_seconds",  30.0)
                mode.setdefault("energy_threshold",  0.01)
                mode.setdefault("pre_roll_seconds",  0.25)
                mode.setdefault("lang",  "en")
                mode.setdefault("input_delay",  0.01)
                mode.setdefault("transformer_device",  "auto")
            elif mode["type"] == "vosk":
                path = mode.get("path", None)
                if not path:
                    raise Exception(f"Path of mode {mode.get('name')} is not set")
                mode.setdefault("input_delay",  0.01)
        
        self.starting_mode = data.get("starting_mode", list(self.modes.keys())[0] if len(self.modes) > 0 else None)
