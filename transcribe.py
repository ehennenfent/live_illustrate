#! python3.7

# From https://github.com/davabase/whisper_real_time/blob/master/transcribe_demo.py

import argparse
from datetime import datetime
from queue import Queue
from time import sleep
from threading import Thread

import speech_recognition as sr
import tiktoken
from openai import OpenAI
from functools import lru_cache
from collections import deque
import requests

SYSTEM_PROMPT = "You are a helpful assistant that describes scenes to an artist who wants to draw them. \
You will be given several lines of dialogue that contain details about the physical surroundings of the characters. \
Your job is to summarize the details of the scene in a bulleted list containing 4-7 bullet points. \
If there is more than one scene described by the dialog, summarize only the most recent one. \
Remember to be concise and not include details that cannot be seen."
WAIT_SECONDS = 7.5 * 60
MAX_CONTEXT = 4000  # Probably 15-25 minutes of conversation

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
text_buffer = []


@lru_cache(maxsize=20)
def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def get_last_n_tokens(n: int) -> str:
    if not text_buffer:
        return ""
    system_prompt_tokens = num_tokens_from_string(SYSTEM_PROMPT)
    my_copy = deque(text_buffer)
    context = [my_copy.pop()]
    while (system_prompt_tokens + num_tokens_from_string("\n".join(context))) < MAX_CONTEXT:
        if not my_copy:
            break
        context.append(my_copy.pop())
    return "\n".join(reversed(context))

def save_image(url):
    try:
        r = requests.get((url), stream=True)
        if r.status_code == 200:
            with open("data/" + datetime.now().strftime("%Y_%m_%d-%H_%M_%S") + ".png", "wb") as outf:
                for chunk in r:
                    outf.write(chunk)

    except Exception as e:
        print("failed to write image to file:", e)


def record_callback(_, audio) -> None:
    audio_queue.put(audio.get_raw_data())


def transcription_thread(recorder, model, sample_rate, sample_width):
    print("Starting transcription thread...")
    with open("data/" + datetime.now().strftime("%Y_%m_%d-%H_%M_%S") + ".txt", "w") as outf:
        while True:
            if not audio_queue.empty():
                text = recorder.recognize_whisper(
                    sr.AudioData(audio_queue.get(), sample_rate, sample_width), model=model
                ).strip()
                text_buffer.append(text)
                try:
                    print(datetime.now(), ">", text, file=outf, flush=True)
                except Exception as e:
                    print("failed to write text to file:", e)
            sleep(0.25)


def image_thread():
    print("Starting rendering thread")
    openai_client = OpenAI()

    last_run = datetime.now()
    while True:
        if (datetime.now() - last_run).seconds > WAIT_SECONDS:
            last_run = datetime.now()
            try:
                response = openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": get_last_n_tokens(MAX_CONTEXT)},
                        ]
                    )
                text = response['choices'][-1]['message']['content'].strip()

                rendered = openai_client.images.generate(
                    model="dall-e-3",
                    prompt=text,
                    size="1792×1024",
                    quality="standard",
                    n=1,
                )

                image_url = rendered.data[0].url
                save_image(image_url)
            except Exception as e:
                print("Exception while calling OpenAPI:", e)

        sleep(1)

def main():
    args = get_args()

    # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
    recorder = sr.Recognizer()
    recorder.dynamic_energy_threshold = args.dynamic_energy_threshold
    source = sr.Microphone(sample_rate=16000)

    print("Now listening...")
    with source:
        recorder.adjust_for_ambient_noise(source)
    recorder.listen_in_background(source, record_callback)

    trans_thread = Thread(
        target=transcription_thread, args=(recorder, args.model, source.SAMPLE_RATE, source.SAMPLE_WIDTH), daemon=True
    )
    render_thread = Thread(target=image_thread, daemon=True)

    trans_thread.start()
    render_thread.start()

    while True:
        try:
            sleep(0.5)
        except KeyboardInterrupt:
            print("Bye")
            break


if __name__ == "__main__":
    main()
