import logging
import typing as t

from flask import Flask, Response, send_from_directory

# silence the logging for every single request
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

IMAGE_HTML = """<div hx-get="/image/{index}" hx-trigger="every 5s" hx-swap="outerHTML transition:true" class="imgbox"><img src='{image_url}' class='center-fit'/></div>"""


class ImageServer:
    def __init__(self, host: str, port: int, default_image: str = "https://placehold.co/1792x1024/png") -> None:
        self.host: str = host
        self.port: int = port

        self.images: t.List[str] = [default_image]

        self.app = Flask(__name__)

        self.app.add_url_rule("/", "index", self.serve_index)
        self.app.add_url_rule("/image/<index>", "image", self.serve_image_tag)

    def serve_index(self) -> Response:
        return send_from_directory("templates", "index.html")

    def serve_image_tag(self, index: str) -> str:
        """Sneaky image handler that counts up by index until we get to the most recent image,
        using HTMX to re-request the endpoint every few seconds."""
        if not index.isdigit():
            index = -1
        index = int(index)
        if index not in range(len(self.images)):
            index = -1
        next_index = min(index + 1, len(self.images) - 1)
        return IMAGE_HTML.format(index=next_index, image_url=self.images[next_index])

    def start(self) -> None:
        self.app.run(host=self.host, port=self.port)

    def update_image(self, image_url: str) -> None:
        self.images.append(image_url)
