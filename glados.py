from io import BytesIO
import torch
from utils.tools import prepare_text
from scipy.io.wavfile import write
from sys import modules as mod
from time import time
from tempfile import TemporaryFile
import numpy as np
from discord.player import AudioSource
from discord.opus import Encoder, APPLICATION_VOIP
import struct
from soxr import resample

try:
    import winsound
    import os
    os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = 'C:\Program Files\eSpeak NG\libespeak-ng.dll'
    os.environ['PHONEMIZER_ESPEAK_PATH'] = 'C:\Program Files\eSpeak NG\espeak-ng.exe'
except ImportError:
    from subprocess import call

initialized = False

def initialize():
    global initialized, glados, vocoder, init_vo, init_mel, device
    # Select the device
    if torch.is_vulkan_available():
        device = 'vulkan'
    elif torch.cuda.is_available():
        device = 'cuda'
    else:
        device = 'cpu'

    # Load models
    glados = torch.jit.load('models/glados.pt')
    vocoder = torch.jit.load('models/vocoder-gpu.pt', map_location=device).half()

    # Prepare models in RAM
    for i in range(2):
        init = glados.generate_jit(prepare_text(str(i)))
        init_mel = init['mel_post'].to(device)
        init_vo = vocoder(init_mel)
    
    initialized = True

import json

VOCODER_SR = 22050
OPUS_SR = 24000
ENCODER = None

def setup_encoder():
    global ENCODER
    if ENCODER is None:
        ENCODER = Encoder(APPLICATION_VOIP)
        ENCODER.SAMPLING_RATE = OPUS_SR
        ENCODER.CHANNELS = 1
        ENCODER.SAMPLE_SIZE = struct.calcsize("h") * ENCODER.CHANNELS
        ENCODER.SAMPLES_PER_FRAME = int(ENCODER.SAMPLING_RATE / 1000 * 20)
        ENCODER.FRAME_SIZE = ENCODER.SAMPLES_PER_FRAME * ENCODER.SAMPLE_SIZE
        ENCODER._state = ENCODER._create_state()

setup_encoder()

class VocoderAudio(AudioSource):
    global ENCODER
    def __init__(self, stream: BytesIO) -> None:
        self.stream = stream

    def read(self) -> bytes:
        ret = self.stream.read(ENCODER.FRAME_SIZE)
        if len(ret) == 0:
            return b''
        if len(ret) < ENCODER.FRAME_SIZE:
            arr = bytearray(ret)
            missing = ENCODER.FRAME_SIZE - len(ret)
            arr.extend(b'\x00' * missing)
            ret = bytes(arr)
        
        ret = ENCODER.encode(ret, ENCODER.SAMPLES_PER_FRAME)

        return ret

    def is_opus(self) -> bool:
        return True


def tts(text: str) -> VocoderAudio:
    global initialized, glados, vocoder, init_vo, init_mel, device

    if not initialized:
        initialize()

    # Tokenize, clean and phonemize input text
    x = prepare_text(text).to('cpu')

    with torch.no_grad():

        # Generate generic TTS-output
        tts_output = glados.generate_jit(x)

        # Use HiFiGAN as vocoder to make output sound like GLaDOS
        mel = tts_output['mel_post'].to(device)
        audio = vocoder(mel)
        
        # Normalize audio to fit in wav-file
        audio = audio.squeeze()
        audio = audio * 32768.0
        audio: np.ndarray = audio.cpu().numpy().astype('int16')

        # number_of_samples = round(len(audio) * float(OPUS_SR) / VOCODER_SR)
        resampled = resample(audio, VOCODER_SR, OPUS_SR)

        return VocoderAudio(BytesIO(resampled.tobytes()))


def tts_file(text: str) -> str:
    global initialized, glados, vocoder, init_vo, init_mel, device

    if not initialized:
        initialize()

    # Tokenize, clean and phonemize input text
    x = prepare_text(text).to('cpu')

    with torch.no_grad():

        # Generate generic TTS-output
        tts_output = glados.generate_jit(x)

        # Use HiFiGAN as vocoder to make output sound like GLaDOS
        mel = tts_output['mel_post'].to(device)
        audio = vocoder(mel)
        
        # Normalize audio to fit in wav-file
        audio = audio.squeeze()
        audio = audio * 32768.0
        audio = audio.cpu().numpy().astype('int16')
        output_file = f'output_{int(time())}.wav'
        
        # 22050 = 22,05 kHz sample rate

        
        write(output_file, 22050, audio)

    return output_file

def tts_out(text: str) -> None:
    global initialized, glados, vocoder, init_vo, init_mel, device

    if not initialized:
        initialize()

    # Tokenize, clean and phonemize input text
    x = prepare_text(text).to('cpu')

    with torch.no_grad():

        # Generate generic TTS-output
        tts_output = glados.generate_jit(x)

        # Use HiFiGAN as vocoder to make output sound like GLaDOS
        mel = tts_output['mel_post'].to(device)
        audio = vocoder(mel)
        
        # Normalize audio to fit in wav-file
        audio = audio.squeeze()
        audio = audio * 32768.0
        audio = audio.cpu().numpy().astype('int16')
        
        audio_bytes = BytesIO()

        # 22050 = 22,05 kHz sample rate
        write(audio_bytes, 22050, audio)
        audio_bytes.seek(0, 0)
        # Play audio file
        if 'winsound' in mod:
            winsound.PlaySound(audio_bytes.getbuffer(), winsound.SND_MEMORY)
        else:
            try:
                call(["aplay", "./output.wav"])
            except FileNotFoundError as e:
                call(["pw-play", "./output.wav"])
        return

if __name__ == "__main__":
    initialize()
    while(True):
        text = input("> ")
        tts_out(text)
