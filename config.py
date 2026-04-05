import json

class Config:
    def __init__(self, path):
        self.path = path
        self.reload()

    def reload(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        self.model_name = data.get("model_name", "base")
        self.silence_seconds = data.get("silence_seconds", 0.1)
        self.max_chunk_seconds = data.get("max_chunk_seconds", 30.0)
        self.energy_threshold = data.get("energy_threshold", 0.01)
        self.pre_roll_seconds = data.get("pre_roll_seconds", 0.25)
        self.lang = data.get("lang", "en")
        self.input_delay = data.get("input_delay", 0.01)
        self.paste_shortcut = data.get("paste_shortcut", "ctrl + shift + v")
        self.dictate_prefix = data.get("dictate_prefix", "say")
        self.reload_command = data.get("reload_command", "reload config")
        self.commands = data.get("commands", {})

