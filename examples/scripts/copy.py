import pyperclip

def script(*args):
    text = args[0]
    pyperclip.copy(text)
