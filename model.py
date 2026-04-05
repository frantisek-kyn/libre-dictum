from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq

import whisper

class Model():
    def __init__(self, name):
        splitted = name.split("-")
        self.whisper = False
        if splitted[0] == "whisper":
            self.name = '-'.join(splitted[1:])
            self.model = whisper.load_model(self.name)
            self.whisper = True
        else:
            self.name = name
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(name, device_map="auto")
            self.processor = AutoProcessor.from_pretrained(name)

    def transcribe(self, audio, language: str="en") -> str:
        if self.whisper:
            return self.model.transcribe(audio, language=language)
        else:
            inputs = self.processor(audio, sampling_rate=16000, return_tensors="pt", language=language)
            inputs.to(self.model.device, dtype=self.model.dtype)
            outputs = self.model.generate(**inputs, max_new_tokens=256)
            return self.processor.decode(outputs, skip_special_tokens=True)
        

