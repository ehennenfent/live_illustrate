import argparse
import logging
from pathlib import Path
from threading import Thread
from time import sleep
from webbrowser import open_new_tab

from dotenv import load_dotenv

from .render import ImageRenderer
from .serve import ImageServer
from .session_data import SessionData
from .summarize import TextSummarizer
from .text_buffer import TextBuffer
from .transcribe import AudioTranscriber
from .util import Image, Summary, Transcription, is_transcription_interesting

load_dotenv()

DEFAULT_DATA_DIR = Path(__file__).parent.parent.joinpath("data")


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Automatic live illustration for table-top RPGs")
    parser.add_argument(
        "--audio_model",
        default="medium.en",
        help="Whisper model to use for audio transcription",
        choices=["tiny.en", "base.en", "small.en", "medium.en", "large", "large-v2", "large-v3"],
    )
    parser.add_argument(
        "--wait_minutes",
        default=7.5,
        type=float,
        help="How frequently to summarize the conversation and generate an image",
    )
    parser.add_argument(
        "--phrase_timeout",
        default=0.75,
        type=float,
        help="Period of time after which to force transcription, even without a pause. "
        "Specified as a fraction of wait_minutes",
    )
    parser.add_argument(
        "--max_context",
        default=2000,  # very roughly ten minutes or so?
        type=int,
        help="Maximum number of tokens to summarize from the conversations",
    )
    parser.add_argument(
        "--summarize_model",
        default="gpt-3.5-turbo",
        help="LLM to use for summarizing transcription",
        choices=["gpt-3.5-turbo", "gpt-4"],
    )
    parser.add_argument(
        "--image_model",
        default="dall-e-3",
        help="Diffusion model to use for generating image",
        choices=["dall-e-3", "dall-e-2"],
    )
    parser.add_argument(
        "--image_size",
        default="1792x1024",
        help="Size of image to render (smaller is cheaper)",
        choices=["1792x1024", "1024x1792", "1024x1024", "512x512", "256x256"],
    )
    parser.add_argument(
        "--image_quality",
        default="standard",
        help="How fancy of an image to render",
        choices=["standard", "hd"],
    )
    parser.add_argument(
        "--image_style",
        default="vivid",
        help="How stylized of an image to render",
        choices=["vivid", "natural"],
    )
    parser.add_argument(
        "--server_host",
        default="0.0.0.0",
        help="Address to bind web server",
    )
    parser.add_argument(
        "--server_port",
        default=8080,
        type=int,
        help="Port to serve HTML viewer on",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Automatically open a browser tab for the rendered images",
    )
    parser.add_argument(
        "--persistence_of_memory",
        default=0.2,  # Expressed as a fraction of the total buffered transcription
        type=float,
        help="How much of the previous transcription to retain after generating each summary. 0 - 1.0",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
    )
    return parser.parse_args()


def main() -> None:
    args = get_args()
    logging.basicConfig(format="%(name)s: %(message)s", level=logging.DEBUG if args.verbose > 0 else logging.INFO)

    # tweak loggers for client libraries
    logging.getLogger("httpx").setLevel(logging.INFO if args.verbose > 0 else logging.WARNING)  # used by OpenAI
    logging.getLogger("requests").setLevel(logging.INFO if args.verbose > 0 else logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.INFO if args.verbose > 0 else logging.WARNING)  # flask

    # create each of our thread objects with the apppropriate command line args
    transcriber = AudioTranscriber(model=args.audio_model, phrase_timeout=args.wait_minutes * args.phrase_timeout)
    buffer = TextBuffer(
        wait_minutes=args.wait_minutes, max_context=args.max_context, persistence=args.persistence_of_memory
    )
    summarizer = TextSummarizer(model=args.summarize_model)
    renderer = ImageRenderer(
        model=args.image_model,
        image_size=args.image_size,
        image_quality=args.image_quality,
        image_style=args.image_style,
    )
    server = ImageServer(
        host=args.server_host, port=args.server_port, default_image=f"https://placehold.co/{args.image_size}/png"
    )

    with SessionData(DEFAULT_DATA_DIR, echo=True) as session_data:
        # wire up some callbacks to save the intermediate data and forward it along
        def on_text_transcribed(transcription: Transcription) -> None:
            if is_transcription_interesting(transcription):
                session_data.save_transcription(transcription)
                buffer.send(transcription)

        def on_summary_generated(summary: Summary | None) -> None:
            if summary:
                session_data.save_summary(summary)
                renderer.send(summary)

        def on_image_rendered(image: Image | None) -> None:
            if image:
                server.update_image(image)
                session_data.save_image(image)

        # start each thread with the appropriate callback
        Thread(target=transcriber.start, args=(on_text_transcribed,), daemon=True).start()
        Thread(target=summarizer.start, args=(on_summary_generated,), daemon=True).start()
        Thread(target=renderer.start, args=(on_image_rendered,), daemon=True).start()

        # Buffer has two threads running at once - one to just pull text from the queue and
        # append it to the buffer, and one to wake up every few minutes and grab the context
        # for summarizing.
        Thread(target=buffer.start, args=(lambda _len: None,), daemon=True).start()
        Thread(target=buffer.buffer_forever, args=(summarizer.send,), daemon=True).start()

        if args.open:
            # opening the browser tab automatically doesn't seem to work through WSL
            def open_browser() -> None:
                sleep(2)
                open_new_tab(f"http://{args.server_host}:{args.server_port}")

            Thread(target=lambda: open_browser).start()

        # flask feels like it probably has a good ctrl+c handler, so we'll make this one the main thread
        server.start()


if __name__ == "__main__":
    main()
