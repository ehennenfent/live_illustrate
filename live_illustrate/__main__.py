import argparse
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

load_dotenv()

DEFAULT_DATA_DIR = Path(__file__).parent.parent.joinpath("data")


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
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
        "--max_context",
        default=2000,
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
        choices=["dall-e-3"],
    )
    parser.add_argument(
        "--image_size",
        default="1792x1024",
        help="Size of image to render (smaller is cheaper)",
        choices=["1792x1024", "1024x1024"],
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
    return parser.parse_args()


def main() -> None:
    with SessionData(DEFAULT_DATA_DIR, echo=True) as session_data:
        args = get_args()

        transcriber = AudioTranscriber(model=args.audio_model)
        buffer = TextBuffer(wait_minutes=args.wait_minutes, max_context=args.max_context)
        summarizer = TextSummarizer(model=args.summarize_model)
        renderer = ImageRenderer(model=args.image_model, image_size=args.image_size)
        server = ImageServer(host=args.server_host, port=args.server_port)

        def on_image_rendered(url: str) -> None:
            session_data.save_image(url)
            server.update_image(url)

        def on_text_transcribed(text: str) -> None:
            session_data.save_transcription(text)
            buffer.send(text)

        def on_summary_generated(text: str) -> None:
            session_data.save_summary(text)
            renderer.send(text)

        Thread(target=transcriber.start, args=(on_text_transcribed,), daemon=True).start()
        Thread(target=summarizer.start, args=(on_summary_generated,), daemon=True).start()
        Thread(target=renderer.start, args=(on_image_rendered,), daemon=True).start()
        Thread(target=buffer.start, args=(lambda _len: None,), daemon=True).start()
        Thread(target=buffer.buffer_forever, args=(summarizer.send,), daemon=True).start()

        if args.open:

            def open_browser() -> None:
                sleep(2)
                open_new_tab(f"http://{args.server_host}:{args.server_port}")

            Thread(target=lambda: open_browser).start()

        server.start()


if __name__ == "__main__":
    main()
