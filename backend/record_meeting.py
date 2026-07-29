import sounddevice as sd
from scipy.io.wavfile import write

duration = 30  # seconds
fs = 44100

print("Recording meeting...")

recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)

sd.wait()

write("meeting.wav", fs, recording)

print("Recording saved as meeting.wav")