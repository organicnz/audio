import os
import tornado.ioloop
import tornado.web
import tornado.websocket
import json

class AudioStreamHandler(tornado.websocket.WebSocketHandler):
    clients = set()  # Store connected clients

    def check_origin(self, origin):
        return True

    def open(self):
        self.clients.add(self)
        print("WebSocket opened")
        self.send_recordings()

    def on_message(self, message):
        if isinstance(message, bytes):
            filename = f"recording_{len(os.listdir('recordings')) + 1}.wav"
            try:
                with open(f"recordings/{filename}", "wb") as f:
                    f.write(message)
                print(f"Audio saved as {filename}")
                self.send_recordings()
            except Exception as e:
                print(f"Error saving file: {e}")
        elif isinstance(message, str):
            data = json.loads(message)
            if data.get('action') == 'refresh':
                self.send_recordings()

    def send_recordings(self):
        recordings = os.listdir('recordings')
        for client in self.clients:
            client.write_message(json.dumps(recordings))

    def on_close(self):
        self.clients.remove(self)
        print("WebSocket closed")

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("audio_client.html")

class DeleteRecordingHandler(tornado.web.RequestHandler):
    def delete(self, filename):
        try:
            os.remove(os.path.join("recordings", filename))
            self.set_status(204)  # No Content
            print(f"Deleted {filename}")
            AudioStreamHandler.send_recordings(AudioStreamHandler)
        except Exception as e:
            self.set_status(500)
            print(f"Error deleting file {filename}: {e}")

class AudioFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        # Set permissive CORS header for audio playback
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
    print("Server started on http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()