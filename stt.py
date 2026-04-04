import queue
import threading
from collections import deque

import numpy as np
import pyperclip
import sounddevice as sd
import whisper


class WhisperStream:
    def __init__(
        self,
        model_name: str = "base",
        sample_rate: int = 16000,
        block_duration: float = 0.1,
        silence_seconds: float = 2.0,
        max_chunk_seconds: float = 10.0,
        energy_threshold: float = 0.01,
        pre_roll_seconds: float = 0.25,
        chunk_callback=None,
        lang = "en"
    ):
        self.model = whisper.load_model(model_name)
        self.sample_rate = sample_rate
        self.block_duration = block_duration
        self.silence_seconds = silence_seconds
        self.max_chunk_seconds = max_chunk_seconds
        self.energy_threshold = energy_threshold
        self.pre_roll_seconds = pre_roll_seconds
        self.chunk_callback = chunk_callback

        self._audio_q = queue.Queue()
        self._stop_event = threading.Event()
        self._worker = None
        self._stream = None
        self.text = ""
        self.lang = lang

    def start(self):
        """Begin capturing audio and transcribing chunk by chunk."""
        self.text = ""
        self._stop_event.clear()

        def callback(indata, frames, time_info, status):
            if status:
                print(status)
            self._audio_q.put(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=callback,
            blocksize=int(self.sample_rate * self.block_duration),
        )
        self._stream.start()

        self._worker = threading.Thread(target=self._transcribe_loop, daemon=True)
        self._worker.start()

    def end(self):
        """Stop capture and copy the final transcript to the clipboard."""
        self._stop_event.set()

        if self._worker is not None:
            self._worker.join(timeout=5)

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        return self.text.strip()

    def _rms(self, audio: np.ndarray) -> float:
        audio = np.asarray(audio, dtype=np.float32)
        if audio.size == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(audio))))

    def _transcribe_loop(self):
        pre_roll_max_blocks = max(1, int(self.pre_roll_seconds / self.block_duration))
        pre_roll = deque(maxlen=pre_roll_max_blocks)

        recording = False
        current_chunk = []
        chunk_seconds = 0.0
        silence_seconds = 0.0

        while not self._stop_event.is_set() or not self._audio_q.empty():
            try:
                block = self._audio_q.get(timeout=0.2)
            except queue.Empty:
                continue

            block = np.asarray(block, dtype=np.float32).reshape(-1)
            block_len_seconds = len(block) / self.sample_rate
            level = self._rms(block)

            if not recording:
                pre_roll.append(block)

                if level >= self.energy_threshold:
                    recording = True
                    current_chunk = list(pre_roll)
                    pre_roll.clear()
                    chunk_seconds = sum(len(x) for x in current_chunk) / self.sample_rate
                    silence_seconds = 0.0
                continue

            current_chunk.append(block)
            chunk_seconds += block_len_seconds

            if level < self.energy_threshold:
                silence_seconds += block_len_seconds
            else:
                silence_seconds = 0.0

            should_end = (
                silence_seconds >= self.silence_seconds
                or chunk_seconds >= self.max_chunk_seconds
            )

            if should_end:
                audio = np.concatenate(current_chunk, axis=0).flatten()
                text = self._transcribe_audio(audio)

                if text:
                    text = text.strip()
                    self.text += (" " if self.text else "") + text
                    if self.chunk_callback:
                        self.chunk_callback(text)

                recording = False
                current_chunk = []
                chunk_seconds = 0.0
                silence_seconds = 0.0
                pre_roll.clear()

        # Flush final partial chunk
        if current_chunk:
            audio = np.concatenate(current_chunk, axis=0).flatten()
            text = self._transcribe_audio(audio)
            if text:
                text = text.strip()
                self.text += (" " if self.text else "") + text
                if self.chunk_callback:
                    self.chunk_callback(text)

    def _transcribe_audio(self, audio: np.ndarray) -> str:
        if audio.size == 0:
            return ""
        result = self.model.transcribe(audio, fp16=False, language=self.lang)
        return result.get("text", "")

if __name__ == "__main__":
    #Example usage:
    def callback(text):
        print(text)
    ws = WhisperStream(
        model_name="turbo",
        silence_seconds=1.0,
        max_chunk_seconds=30.0,
        energy_threshold=0.01,
        chunk_callback = callback
    )
    ws.start()
    input("Recording... press Enter to stop.\n")
    final_text = ws.end()
    pyperclip.copy(final_text)
    print(final_text)
