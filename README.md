
# Overview

 A minimalist accessibility tool for GNU/Linux. It bridges local speech recognition with kernel-level input simulation. This bypasses limitations of specific window managers or desktop environments.
 
https://github.com/user-attachments/assets/c7735d22-9583-4e38-a2c0-72d622a4153f

## Features

* **Direct Kernel-Level Input**: `python-evdev` injects keystrokes directly into the input subsystem, meaning it can work even in a TTY.
* **Local Processing**: Relies purely on local models.
* **Hybrid Transcription**: Utilizes the VOSK models with grammar based on your commands and transformer models for dictation.
* **Mode Switching**: You can switch between different configs on the fly via a voice command.
* **Configurability**: Command structure is fully customizable.
* **System Tray**: Provides live feedback on the current enabled voice mode.
* **Script Execution**: You can execute your own scripts via voice commands.

## Installation
### 1. PyTorch

The installation procedure differs based on your target hardware. For NVIDIA GPU, you can skip this step.

### AMD GPU
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm7.2
```
### CPU
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

For additional information concerning the PyTorch library, visit the official [PyTorch installation guide](https://pytorch.org/get-started/locally/).

### 2. Libre Dictum

While in the folder of this repository, execute

```bash
pip install -e .
```

Afterwards, you can launch the application via `libre-dictum`.

### 3. Optional Features

Execute the following commands to install depedencies for additional features:

### systray
Shows the currently enabled voice mode via a coloured circle in the systray.
```bash
pip install -e.[system-tray]
```

### transformer
Enables support for arbitrary transformer models (each transformer model may have its own extra dependencies).
```bash
pip install -e.[transformer]
```

### openai-whisper
Enables support for the openai-whisper model.
```bash
pip install -e.[whisper]
```

### all
You can enable all optional features via
```bash
pip install -e.[all]
```

## Status

In rapid development; config structure is updated often. Currently functional and satisfies many use cases.
