# fuch/main.py
from fuch.listen import listen
from fuch.brain import ask_llm
from fuch.speak import speak
from fuch.actions import open_app
from fuch.brain import ask_llm, detect_open_app

def main():
    speak("FUCH is awake. Meow.")
    while True:
        try:
            text = listen()
            if not text:
                continue

            if text.lower() in ("exit", "quit", "sleep"):
                speak("Fine. I nap now. Purr.")
                break

            reply = ask_llm(text)
            speak(reply)

        except KeyboardInterrupt:
            speak("Interrupted. Rude. Meow.")
            break
        app = detect_open_app(text)

        if app:
            success = open_app(app)
            if success:
                speak(f"Opening {app}. Meow.")
            else:
                speak(f"I couldn't open {app}. Meow.")
                continue


if __name__ == "__main__":
    main()
