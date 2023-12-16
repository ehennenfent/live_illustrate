from flask import Flask, Response, send_from_directory

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class ImageServer:
    image_url: str = "https://placehold.co/1792x1024/png"

    def __init__(self, host: str, port: int) -> None:
        self.host: str = host
        self.port: int = port

        self.app = Flask(__name__)

        self.app.add_url_rule("/", "index", self.serve_index)
        self.app.add_url_rule("/image", "image", self.serve_image_tag)

    def serve_index(self) -> Response:
        return send_from_directory("templates", "index.html")

    def serve_image_tag(self) -> str:
        return f"<img src='{self.image_url}' class='center-fit'/>"

    def start(self) -> None:
        self.app.run(host=self.host, port=self.port)

    def update_image(self, image_url: str) -> None:
        self.image_url = image_url
