import tornado.ioloop
import tornado.web
import tornado.websocket
import json
import wave
import os
import base64

class AudioStreamHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        data = json.loads(message)
        if data['event'] == 'audio':
            audio_data = base64.b64decode(data['data'].split(',')[1])
            filename = f"recording_{len(os.listdir('recordings')) + 1}.wav"
            with wave.open(f"recordings/{filename}", "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                wf.writeframes(audio_data)
            print(f"Audio saved as {filename}")

    def on_close(self):
        print("WebSocket closed")

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("audio_client.html")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/ws", AudioStreamHandler),
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