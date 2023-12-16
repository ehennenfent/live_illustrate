from flask import Flask, send_from_directory


class ImageServer:
    image_url: str = "https://placehold.co/1792x1024/png"

    def __init__(self, host, port) -> None:
        self.host = host
        self.port = port

        self.app = Flask(__name__)

        self.app.add_url_rule("/", "index", self.serve_index)
        self.app.add_url_rule("/image", "image", self.serve_image_tag)

    def serve_index(self):
        return send_from_directory("templates", "index.html")

    def serve_image_tag(self):
        return f"<img src='{self.image_url}' class='center-fit'/>"

    def start(self):
        self.app.run(host=self.host, port=self.port)

    def update_image(self, image_url: str):
        self.image_url = image_url
