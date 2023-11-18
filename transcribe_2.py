#! python3.7

import argparse
import io
import os
import speech_recognition as sr
import whisper

from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from time import sleep
from sys import platform


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="medium.en", help="Model to use",
                        choices=["tiny.en", "base.en", "small.en", "medium.en", "large", "large-v2", "large-v3"])
    parser.add_argument("--energy_threshold", default=1000,
                        help="Energy level for mic to detect.", type=int)
    parser.add_argument("--record_timeout", default=2,
                        help="How real time the recording is in seconds.", type=float)
    parser.add_argument("--phrase_timeout", default=3,
                        help="How much empty space between recordings before we "
                             "consider it a new line in the transcription.", type=float)
    args = parser.parse_args()

    # Thread safe Queue for passing data from the threaded recording callback.
    data_queue = Queue()
    # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    # Definitely do this, dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.
    recorder.dynamic_energy_threshold = False

    source = sr.Microphone(sample_rate=16000)

    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(recognizer, audio:sr.AudioData) -> None:
        try:
            print("transcribing...")
            transcribed = recognizer.recognize_whisper(audio, model=args.model)
            data_queue.put(transcribed)
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Whisper; {0}".format(e))

    # Create a background thread that will pass us raw audio bytes.
    # We could do this manually but SpeechRecognizer provides a nice helper.
    recorder.listen_in_background(source, record_callback)# , phrase_time_limit=args.record_timeout)

    # Cue the user that we're ready to go.
    print("Starting to listen...\n")

    while True:
        try:
            if not data_queue.empty():
                print(data_queue.get())
                # Infinite loops are bad for processors, must sleep.
                sleep(0.25)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()