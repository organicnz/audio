import os
import tornado.ioloop
import tornado.web
import tornado.websocket
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioStreamHandler(tornado.websocket.WebSocketHandler):
    clients = set()

    def check_origin(self, origin):
        return True

    def open(self):
        self.clients.add(self)
        logger.info("WebSocket opened")
        self.send_recordings()

    def on_message(self, message):
        if isinstance(message, bytes):
            logger.info(f"Received audio data of size: {len(message)} bytes")
            filename = f"recording_{len(os.listdir('recordings')) + 1}.wav"
            try:
                with open(os.path.join('recordings', filename), "wb") as f:
                    f.write(message)
                logger.info(f"Audio saved as {filename}")
                self.send_recordings()
            except Exception as e:
                logger.error(f"Error saving file: {e}")
        elif isinstance(message, str):
            try:
                data = json.loads(message)
                if data.get('action') == 'refresh':
                    self.send_recordings()
            except json.JSONDecodeError:
                logger.error("Received invalid JSON")

    def send_recordings(self):
        recordings = [f for f in os.listdir('recordings') if f.endswith('.wav')]
        for client in self.clients:
            client.write_message(json.dumps(recordings))

    def on_close(self):
        self.clients.remove(self)
        logger.info("WebSocket closed")

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("audio_client.html")

class DeleteRecordingHandler(tornado.web.RequestHandler):
    def delete(self, filename):
        try:
            os.remove(os.path.join("recordings", filename))
            self.set_status(204)
            logger.info(f"Deleted {filename}")
            AudioStreamHandler.send_recordings(AudioStreamHandler)
        except Exception as e:
            self.set_status(500)
            logger.error(f"Error deleting file {filename}: {e}")

class AudioFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Access-Control-Allow-Origin", "*")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/ws", AudioStreamHandler),
        (r"/delete/(.+)", DeleteRecordingHandler),
        (r"/recordings/(.*)", AudioFileHandler, {"path": "recordings"}),
    ],
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    debug=True)

if __name__ == "__main__":
    if not os.path.exists("recordings"):
        os.makedirs("recordings")
    app = make_app()
    app.listen(8888)
    logger.info("Server started on http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()