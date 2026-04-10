import json
import warnings
from copy import deepcopy
from typing import Any, Dict

from pathlib import Path

class Config:
    def __init__(self, path):
        self.path = path
        self.reload()

    _keys_not_to_add = ["type", "imports"]
    _keys_not_to_merge = ["icon", "imports"]

    _default_mode = {
        "type": "import",
        "icon": None,
        "commands": {},
        "aliases": {},
        "banned_strings": [],
        "input_delay": 0.01,
        "enter_command": None,
        "exit_command": None,
        "transformer": {
            "silence_seconds": 0.3,
            "max_chunk_seconds": 30.0,
            "energy_threshold": 0.01,
            "pre_roll_seconds": 0.25,
            "lang": "en",
            "transformer_device": "auto"
        }
    }

    def _import_mode(self, mode1: Dict[str, Any], mode2: Dict[str, Any]) -> None:
        def merge(target: Dict[str, Any], source: Dict[str, Any]) -> None:
            target_type = target.get("type")

            for key, value in source.items():
                if key in self._keys_not_to_add:
                    continue

                # Special handling for transformer / vosk
                if key in ("transformer", "vosk") and isinstance(value, dict):
                    if target_type == key:
                        merge(target, value)
                    continue

                if key not in target:
                    target[key] = deepcopy(value)
                    continue

                existing = target[key]
                if key in self._keys_not_to_merge:
                    continue
                elif isinstance(existing, dict) and isinstance(value, dict):
                    merge(existing, value)
                elif isinstance(existing, list) and isinstance(value, list):
                    existing.extend(deepcopy(value))

        merge(mode1, mode2)

    def _append_imports(self, mode: Dict[str, Any]) -> None:
        for mode_key in mode.get("imports", []):
            if mode_key not in self.modes:
                raise Exception(f"Mode {mode_key} needed for import was not found.")
            imported_mode = self.modes[mode_key]
            self._import_mode(mode, imported_mode)

    
    def _create_config_dir(self) -> None:
        self.script_path = self.path / "scripts"
        self.config_path = self.path / "config.json"
        if not (self.script_path.exists() and self.script_path.is_dir()):
            # Function to create the directory
            self.script_path.mkdir(parents=True, exist_ok=True)

    def reload(self) -> None:
        self._create_config_dir()
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            file_missing = False
        except FileNotFoundError:
            warnings.warn(f"Configuration file '{self.config_path}' is missing. Using defaults.", UserWarning)
            file_missing = True
            data = {}
        self.reload_command = data.get("reload_command", "reload config")
        self.modes = data.get("modes", {})
        self.enable_systray = data.get("enable_systray", False)
        self.imports = []
        for mode_name, mode in self.modes.items():
            self._append_imports(mode)
            mode.setdefault("type", "import")
            if mode["type"] != "import":
                self._import_mode(mode, self._default_mode)
            if mode["type"] == "vosk":
                if not mode.get("path", None):
                    raise Exception(f"Path of model in mode {mode_name} is not set")
            elif mode["type"] == "transformer":
                if not mode.get("model_name", None):
                    raise Exception(f"Model name in mode {mode_name} is not set")
        for key in list(self.modes.keys()):
            if self.modes[key].get("type") == "import":
                self.modes.pop(key)
                self.imports.append(key)
        
        self.starting_mode = data.get("starting_mode", list(self.modes.keys())[0] if len(self.modes) > 0 else None)
