import json

class Config:
    def __init__(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.model_name = data.get("model_name", "base")
        self.silence_seconds = data.get("silence_seconds", 1.0)
        self.max_chunk_seconds = data.get("max_chunk_seconds", 30.0)
        self.energy_threshold = data.get("energy_treshold", 0.01)
        self.pre_roll_seconds = data.get("pre_roll_seconds", 0.25)
        self.lang = data.get("lang", "en")
        self.command_prefix = data.get("command_prefix", "command")
        self.commands = data.get("commands", {})

