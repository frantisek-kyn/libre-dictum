from evdev import UInput, ecodes as e
import time

char_map = {
    'a': e.KEY_A, 'b': e.KEY_B, 'c': e.KEY_C, 'd': e.KEY_D,
    'e': e.KEY_E, 'f': e.KEY_F, 'g': e.KEY_G, 'h': e.KEY_H,
    'i': e.KEY_I, 'j': e.KEY_J, 'k': e.KEY_K, 'l': e.KEY_L,
    'm': e.KEY_M, 'n': e.KEY_N, 'o': e.KEY_O, 'p': e.KEY_P,
    'q': e.KEY_Q, 'r': e.KEY_R, 's': e.KEY_S, 't': e.KEY_T,
    'u': e.KEY_U, 'v': e.KEY_V, 'w': e.KEY_W, 'x': e.KEY_X,
    'y': e.KEY_Y, 'z': e.KEY_Z,
    '0': e.KEY_0, '1': e.KEY_1, '2': e.KEY_2, '3': e.KEY_3,
    '4': e.KEY_4, '5': e.KEY_5, '6': e.KEY_6, '7': e.KEY_7,
    '8': e.KEY_8, '9': e.KEY_9,
    'space': e.KEY_SPACE,
    '.': e.KEY_DOT,
    ',': e.KEY_COMMA,
    ';': e.KEY_SEMICOLON,
    "'": e.KEY_APOSTROPHE,
    '-': e.KEY_MINUS,
    '=': e.KEY_EQUAL,
    '/': e.KEY_SLASH,
    '\\': e.KEY_BACKSLASH,
    '[': e.KEY_LEFTBRACE,
    ']': e.KEY_RIGHTBRACE,
    'enter': e.KEY_ENTER,
    'shift': e.KEY_LEFTSHIFT, 'ctrl': e.KEY_LEFTCTRL, 'alt': e.KEY_LEFTALT
}

holdable_keys = ["shift", "ctrl", "alt"]

keys_held = []

def handle_input(text):
    ui = UInput()
    data = text.replace(" ", "").lower().split("+")
    for char in data:
        if char not in char_map:
            raise Exception(f"{char} is not valid key")
        key = char_map[char]
        ui.write(e.EV_KEY, key, 1)
        ui.syn()
        time.sleep(0.03)
        print(f"{char}: 1")

        if char in holdable_keys:
            keys_held.append(key)
            continue
        
        ui.write(e.EV_KEY, key, 0)
        ui.syn()
        time.sleep(0.03)
        print(f"{char}:0")

        for hold_key in keys_held:
            ui.write(e.EV_KEY, hold_key, 0)
        ui.syn()
        time.sleep(0.03)
    ui.close()

if __name__ == "__main__":
    time.sleep(1)
    handle_input("ctrl + V")
    handle_input("space")
