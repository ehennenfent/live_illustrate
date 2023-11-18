#! python3.7

# From https://github.com/davabase/whisper_real_time/blob/master/transcribe_demo.py

import argparse
from datetime import datetime
from queue import Queue
from time import sleep
from threading import Thread

import speech_recognition as sr


def get_args():
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
    return parser.parse_args()


audio_queue = Queue()
text_queue = Queue()


def record_callback(_, audio) -> None:
    audio_queue.put(audio.get_raw_data())


def transcription_thread(recorder, model, sample_rate, sample_width):
    with open("data/" + datetime.now().strftime("%Y_%m_%d-%H_%M_%S") + ".txt", "w") as outf:
        while True:
            if not audio_queue.empty():
                text = recorder.recognize_whisper(
                    sr.AudioData(audio_queue.get(), sample_rate, sample_width), model=model
                ).strip()
                text_queue.put(text)
                print(text, file=outf, flush=True)
            sleep(0.25)


def main():
    args = get_args()

    # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
    recorder = sr.Recognizer()
    recorder.dynamic_energy_threshold = args.dynamic_energy_threshold
    source = sr.Microphone(sample_rate=16000)

    with source:
        recorder.adjust_for_ambient_noise(source)
    recorder.listen_in_background(source, record_callback)

    print("Now listening...")
    trans_thread = Thread(
        target=transcription_thread, args=(recorder, args.model, source.SAMPLE_RATE, source.SAMPLE_WIDTH), daemon=True
    )
    trans_thread.start()

    while True:
        try:
            while not text_queue.empty():
                print(text_queue.get())
            sleep(0.25)
        except KeyboardInterrupt:
            print("Bye")
            break


if __name__ == "__main__":
    main()
