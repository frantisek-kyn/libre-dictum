import json
import queue
import time
import threading
import sounddevice as sd
from vosk import Model, KaldiRecognizer

import re

class VoskStream:
    def __init__(self, command_keys, other_words = [], model_path="model", sample_rate=16000, chunk_callback=None):
        self.sample_rate = sample_rate
        self.chunk_callback = chunk_callback
        
        self.word_index = 0

        self.model = Model(model_path)
        self.enabled = False
        
        self.keys = list(command_keys)
        vocabulary = list(self.keys)
        if other_words:
            vocabulary.extend(other_words)
        vocabulary.extend(["[unk]"])
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

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def _match_pattern(self, partial_text):
        for template in reversed(self.keys):
            regex_pattern = re.escape(template)
    
            # {any} -> any non-whitespace sequence
            regex_pattern = regex_pattern.replace(r'\{any\}', r'(\S+)')
    
            regex_pattern += r'$'
    
            match = re.search(regex_pattern, partial_text)
            if match:
                return match.group(0)
        return None

    def _transcribe_loop(self):
        while not self._stop_event.is_set():
            try:
                block = self._audio_q.get(timeout=0.2)
            except queue.Empty:
                continue

            if not self.enabled:
                continue

            if self.recognizer.AcceptWaveform(block):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "").strip()
                splitted_text = text.split(' ')
                new_text = ' '.join(splitted_text[self.word_index:])


                if new_text and self.chunk_callback:
                    self.chunk_callback(new_text)
                self.word_index = 0
            else:
                partial_result = json.loads(self.recognizer.PartialResult())
                partial_text = partial_result.get("partial", "").strip()
                
                if not partial_text:
                    continue

                #if "[unk]" in partial_text:
                #    self.recognizer.Reset()
                #    continue
                splitted_text = partial_text.split(' ')
                new_partial_text = ' '.join(splitted_text[self.word_index:])



                regex_match = self._match_pattern(new_partial_text)
                if regex_match:
                    if self.chunk_callback:
                        self.chunk_callback(regex_match)
                    self.word_index = len(splitted_text)
                    #self.recognizer.Reset()
                else:
                    print(new_partial_text)
