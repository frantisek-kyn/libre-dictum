from evdev import UInput, ecodes as e
import time
import re
import subprocess
import importlib

import warnings

import sys

from typing import Iterable

char_map = {
    # Alphabet
    'a': e.KEY_A, 'b': e.KEY_B, 'c': e.KEY_C, 'd': e.KEY_D,
    'e': e.KEY_E, 'f': e.KEY_F, 'g': e.KEY_G, 'h': e.KEY_H,
    'i': e.KEY_I, 'j': e.KEY_J, 'k': e.KEY_K, 'l': e.KEY_L,
    'm': e.KEY_M, 'n': e.KEY_N, 'o': e.KEY_O, 'p': e.KEY_P,
    'q': e.KEY_Q, 'r': e.KEY_R, 's': e.KEY_S, 't': e.KEY_T,
    'u': e.KEY_U, 'v': e.KEY_V, 'w': e.KEY_W, 'x': e.KEY_X,
    'y': e.KEY_Y, 'z': e.KEY_Z,

    # Numeric
    '0': e.KEY_0, '1': e.KEY_1, '2': e.KEY_2, '3': e.KEY_3,
    '4': e.KEY_4, '5': e.KEY_5, '6': e.KEY_6, '7': e.KEY_7,
    '8': e.KEY_8, '9': e.KEY_9,

    # Symbol
    '.': e.KEY_DOT, ',': e.KEY_COMMA, ';': e.KEY_SEMICOLON,
    "'": e.KEY_APOSTROPHE, '-': e.KEY_MINUS, '=': e.KEY_EQUAL,
    '/': e.KEY_SLASH, '\\': e.KEY_BACKSLASH,
    '[': e.KEY_LEFTBRACE, ']': e.KEY_RIGHTBRACE,

    # Modifier
    'shift': e.KEY_LEFTSHIFT, 'ctrl': e.KEY_LEFTCTRL, 'alt': e.KEY_LEFTALT, 'meta': e.KEY_LEFTMETA, 'win': e.KEY_LEFTMETA,

    # Function
    'f1': e.KEY_F1, 'f2': e.KEY_F2, 'f3': e.KEY_F3, 'f4': e.KEY_F4, 'f5': e.KEY_F5, 'f6': e.KEY_F6,
    'f7': e.KEY_F7, 'f8': e.KEY_F8, 'f9': e.KEY_F9, 'f10': e.KEY_F10, 'f11': e.KEY_F11, 'f12': e.KEY_F12,
    'f13': e.KEY_F13, 'f14': e.KEY_F14, 'f15': e.KEY_F15, 'f16': e.KEY_F16, 'f17': e.KEY_F17, 'f18': e.KEY_F18,
    'f19': e.KEY_F19, 'f20': e.KEY_F20, 'f21': e.KEY_F21, 'f22': e.KEY_F22, 'f23': e.KEY_F23, 'f24': e.KEY_F24,

    # Navigation
    'up': e.KEY_UP, 'down': e.KEY_DOWN, 'left': e.KEY_LEFT, 'right': e.KEY_RIGHT, 'home': e.KEY_HOME,
    'end': e.KEY_END, 'pageup': e.KEY_PAGEUP, 'pagedown': e.KEY_PAGEDOWN, 'insert': e.KEY_INSERT,
    'delete': e.KEY_DELETE, 'esc': e.KEY_ESC, 'tab': e.KEY_TAB, 'enter': e.KEY_ENTER, 'backspace': e.KEY_BACKSPACE,
    'space': e.KEY_SPACE
}

mouse_map = {
    'left_mouse': e.BTN_LEFT, 
    'right_mouse': e.BTN_RIGHT
}

modifier_keys = ["shift", "ctrl", "alt", "meta", "win"]

modifiers_held = []

keys_held = []

variables_saved = []

_PLACEHOLDER_RE = re.compile(r"\{(\d+)(?:=([^{}]*))?\}")

def expand_command(response_template: str, values: Iterable[str], apply_defaults: bool = False) -> str:
    values = list(values)
    n_values = len(values)

    def repl(match: re.Match[str]) -> str:
        index = int(match.group(1))
        default = match.group(2)

        if index <= n_values:
            return values[index - 1]

        if apply_defaults:
            return default if default is not None else ""

        new_index = index - n_values
        if default is not None:
            return f"{{{new_index}={default}}}"
        return f"{{{new_index}}}"

    return _PLACEHOLDER_RE.sub(repl, response_template)

def apply_aliases(text, aliases):
    result = text
    for key, value in aliases.items():
        result = re.sub(key, value, result)
    return result

num_words = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
}

def append_script_path(path):
    sys.path.append(path)

pattern = re.compile(r"\b(" + "|".join(num_words) + r")\b")

def replace_number_words(text: str) -> str:
    return pattern.sub(lambda m: num_words[m.group(0)], text)

def expand_repeats(text: str) -> str:
    pattern = re.compile(r"(\d+)\(([^()]*)\)")

    while True:
        new_text = pattern.sub(
                lambda m: "+".join([m.group(2)] * int(m.group(1))),
                text
            )
        if new_text == text:
            return text
        text = new_text

ui = UInput()

exec_regex = r"exec\((.*)\)"

def handle_exec(text):
    match = re.fullmatch(exec_regex, text, re.DOTALL)
    if not match:
        return False
    captured = match.group(1)
    subprocess.run(captured.split(" "))
    return True

python_regex = r"python\((.*)\)"

def handle_python(text):
    match = re.fullmatch(python_regex, text, re.DOTALL)
    if not match:
        return False
    captured = match.group(1)
    exec(captured)
    return True

script_regex = r"script\((.*)\)"

def handle_script(text):
    match = re.fullmatch(script_regex, text, re.DOTALL)
    if not match:
        return False
    captured = match.group(1)
    arguments = captured.split(";;")
    script_path = f"scripts.{arguments.pop(0)}"
    script_function = getattr(importlib.import_module(script_path), "script")
    script_function(*arguments)
    return True

mode_regex = r"mode\((.*)\)"

def handle_mode_change(text, callback):
    match = re.fullmatch(mode_regex, text, re.DOTALL)
    if not match:
        return False
    if not callback:
        warnings.warn(f"Callback function is missing.")
        return True
    captured = match.group(1)
    callback(captured)
    return True

hold_regex = r"hold\((.*)\)"

def handle_hold(text):
    match = re.fullmatch(hold_regex, text, re.DOTALL)
    if not match:
        return (False, text)
    captured = match.group(1)
    return (True, captured)

release_regex = r"release\((.*)\)"

def handle_release(text):
    match = re.fullmatch(release_regex, text, re.DOTALL)
    if not match:
        return (False, text)
    captured = match.group(1)
    return (True, captured)

toggle_regex = r"toggle\((.*)\)"

def handle_toggle(text):
    match = re.fullmatch(toggle_regex, text, re.DOTALL)
    if not match:
        return (False, False, text)
    captured = match.group(1)
    return (True, captured in keys_held, captured)

save_regex = r"save\((.*)\)"

def handle_save(text):
    match = re.fullmatch(save_regex, text, re.DOTALL)
    if not match:
        return False
    captured = match.group(1)
    variables_saved.append(captured)
    return True

combined_regex = re.compile(f"{script_regex}|{python_regex}|{exec_regex}|{mode_regex}|{hold_regex}|{release_regex}|{toggle_regex}|{save_regex}", re.DOTALL)

def handle_input(text, input_delay = 0.01, aliases = {}, script_path = None, mode_change_callback = None):
    text = apply_aliases(text, aliases)
    text = expand_command(text, variables_saved, apply_defaults = True)
    print(text)
    text = expand_repeats(text)
    data = [x.strip().replace(r"\+", "+") for x in re.split(r"(?<!\\)\+", text)]
    invalid_chars = [
            repr(char) for char in data
            if char.lower() not in char_map and not combined_regex.fullmatch(char)
        ]
    if invalid_chars:
        warnings.warn(f"Invalid character(s) found: {', '.join(invalid_chars)}")
        return
    for char in data:
        if handle_mode_change(char, mode_change_callback):
            continue
        if handle_script(char):
            continue
        if handle_python(char):
            continue
        if handle_exec(char):
            continue
        if handle_save(char):
            continue
        else: 
            variables_saved.clear()

        holding, char = handle_hold(char)
        release, char = handle_release(char)
        toggle, toggle_state, char = handle_toggle(char)

        if toggle:
            if toggle_state:
                release = True
            else:
                holding = True

        char = char.lower()
        if char in char_map:
            key = char_map[char]
            target_ui = ui
        elif char in mouse_map:
            key = mouse_map[char]
            target_ui = mouse_ui
        else:
            raise Exception(f"Unknown key {char}")

        if not release:
            if char in keys_held:
                continue
            target_ui.write(e.EV_KEY, key, 1)
            target_ui.syn()
            time.sleep(input_delay)

            if holding:
                keys_held.append(char)
                if key in modifiers_held:
                    modifiers_held.remove(key)
                continue

            if char in modifier_keys:
                modifiers_held.append(key)
                continue
        
        target_ui.write(e.EV_KEY, key, 0)
        target_ui.syn()
        time.sleep(input_delay)

        if release:
            keys_held.remove(char)
            continue

        if len(modifiers_held) != 0:
            for hold_key in modifiers_held[:]:
                target_ui.write(e.EV_KEY, hold_key, 0)
                modifiers_held.remove(hold_key)
            target_ui.syn()
            time.sleep(input_delay)

# Create a virtual mouse device
mouse_capabilities = {
    e.EV_REL: [e.REL_X, e.REL_Y],    
    e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT],

}

mouse_ui = UInput(mouse_capabilities, name="virtual-mouse")

def handle_mouse_relative(dx, dy):
    mouse_ui.write(e.EV_REL, e.REL_X, int(-dx))
    mouse_ui.write(e.EV_REL, e.REL_Y, int(dy))
    mouse_ui.syn()


if __name__ == "__main__":
    time.sleep(1)
    handle_input("ctrl + V")
    handle_input("space")
