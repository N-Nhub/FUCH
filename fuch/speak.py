# fuch/speak.py
import subprocess

ESPEAK_BIN = "/usr/bin/espeak-ng"

def speak(text):
    print(f"🐱 FUCH: {text}")
    subprocess.run([
        ESPEAK_BIN,
        "-v", "en-us+f3",   # female voice variant
        "-p", "75",         # pitch (default ~50)
        "-s", "175",        # speed (default ~160)
        "-a", "110",        # amplitude (soft but audible)
        text
    ])
