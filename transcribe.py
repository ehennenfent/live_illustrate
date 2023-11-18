#! python3.7

# From https://github.com/davabase/whisper_real_time/blob/master/transcribe_demo.py

import argparse
from datetime import datetime
from queue import Queue
from time import sleep

import speech_recognition as sr

data_queue = Queue()


def record_callback(_, audio) -> None:
    data_queue.put(audio.get_raw_data())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default="medium.en",
        help="Model to use",
        choices=[
            "tiny.en",
            "base.en",
            "small.en",
            "medium.en",
            "large",
            "large-v2",
            "large-v3",
        ],
    )
    parser.add_argument(
        "--dynamic_energy_threshold",
        action="store_true",
        default=True,
        help="Adjust the energy threshold dynamically",
    )
    args = parser.parse_args()

    # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
    recorder = sr.Recognizer()
    recorder.dynamic_energy_threshold = args.dynamic_energy_threshold
    source = sr.Microphone(sample_rate=16000)

    with source:
        recorder.adjust_for_ambient_noise(source)
    recorder.listen_in_background(source, record_callback)

    print("Now listening...")

    # open a file with the current datetime as the name, without any special characters
    with open(datetime.now().strftime("%Y_%m_%d-%H_%M_%S") + ".txt", "w") as outf:
        while True:
            try:
                if not data_queue.empty():
                    text = recorder.recognize_whisper(
                        sr.AudioData(data_queue.get(), source.SAMPLE_RATE, source.SAMPLE_WIDTH), model=args.model
                    ).strip()
                    print(text)
                    print(text, file=outf)
                    sleep(0.25)
            except KeyboardInterrupt:
                break


if __name__ == "__main__":
    main()
