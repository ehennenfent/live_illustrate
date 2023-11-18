#! python3.7

# From https://github.com/davabase/whisper_real_time/blob/master/transcribe_demo.py

import argparse
from datetime import datetime
from queue import Queue
from time import sleep
from threading import Thread

import speech_recognition as sr
from openai import OpenAI

SYSTEM_PROMPT = "You are a helpful assistant that describes scenes to people who cannot see them. You will be given several lines of dialogue that contain details about the physical surroundings of the characters. Your job is to describe the details of the scene in a way that makes sense to someone not present. Remember to be concise and descriptive."


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
                try:
                    print(text, file=outf, flush=True)
                except Exception as e:
                    print("failed to write text to file:", e)
            sleep(0.25)


def main():
    args = get_args()

    # openai_client = OpenAI()

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
                text = text_queue.get()
                print(text)
            #     text_buffer.append(text)

            # if len(text_buffer) % 10 == 0:
            #     response = openai_client.chat.completions.create(
            #         model="gpt-3.5-turbo",
            #         messages=[
            #             {"role": "system", "content": SYSTEM_PROMPT},
            #             {"role": "user", "content": "\n".join(text_buffer[-10:])},
            #         ]
            #     )
            #     print(response)

            sleep(0.25)
        except KeyboardInterrupt:
            print("Bye")
            break


if __name__ == "__main__":
    main()
