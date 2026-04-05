# Overview

 A minimalist accessibility tool for GNU/Linux. It bridges local Whisper-based speech recognition with kernel-level input simulation. This bypasses limitations of specific window managers or desktop environments.

# Features

* **Direct Kernel-Level Input**: `python-evdev` injects keystrokes directly into the input subsystem, ensuring compatibility across all GUI and TTY environments.
* **Local Processing**: Whisper turbo for quick private transcription.
* **Configurability**: Command structure is fully customizable. 

# Installation
The installation procedure differs based on your GPU vendor:

### NVIDIA
1. `pip install -r requirements.txt`

### AMD
1. `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm7.2`
2. `pip install -r requirements.txt`

And in the case that you would want to use only your CPU:

1. `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu`
2. `pip install -r requirements.txt`

For additional information, visit the official [PyTorch installation guide](https://pytorch.org/get-started/locally/).

# Status

Highly experimental.
