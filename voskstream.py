import json
import queue
import time
import threading
import sounddevice as sd
from vosk import Model, KaldiRecognizer

class VoskStream:
    def __init__(self, commands_dict, model_path="model", sample_rate=16000, chunk_callback=None):
        self.sample_rate = sample_rate
        self.chunk_callback = chunk_callback
        self.last_word = None
        
        self.model = Model(model_path)
        
        vocabulary = list(commands_dict.keys())
        print(vocabulary)
        self.keys = list(commands_dict.keys())
        vocabulary.extend(["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "[unk]"])
        grammar = json.dumps(vocabulary)
        
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate, grammar)
        
        self._audio_q = queue.SimpleQueue()
        self._stop_event = threading.Event()

    def start(self):
        self._stop_event.clear()

        def callback(indata, frames, time_info, status):
            self._audio_q.put(bytes(indata))

        self._stream = sd.RawInputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            callback=callback,
            blocksize=int(self.sample_rate * 0.1)
        )
        self._stream.start()

        self._worker = threading.Thread(target=self._transcribe_loop, daemon=True)
        self._worker.start()

    def _transcribe_loop(self):
        while not self._stop_event.is_set():
            try:
                block = self._audio_q.get(timeout=0.2)
            except queue.Empty:
                continue

            if self.recognizer.AcceptWaveform(block):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "").strip()
                if text and self.chunk_callback:
                    self.chunk_callback(text)
            else:
                partial_result = json.loads(self.recognizer.PartialResult())
                partial_text = partial_result.get("partial", "").strip()
                
                if not partial_text:
                    continue
                if partial_text == self.last_word:
                    self.recognizer.Reset()
                    self.last_word = None

                if "[unk]" in partial_text:
                    self.recognizer.Reset()
                    continue
                
                if partial_text in self.keys:
                    self.last_word = partial_text.split(" ")[-1]
                    if self.chunk_callback:
                        self.chunk_callback(partial_text)
                    self.recognizer.Reset()
                else:
                    print(partial_text)
