import tornado.ioloop
import tornado.web
import tornado.websocket
import json
import base64
import wave
import os

class AudioStreamHandler(tornado.websocket.WebSocketHandler):
    clients = set()
    audio_data = []

    def check_origin(self, origin):
        return True

    def open(self):
        print("WebSocket opened")
        AudioStreamHandler.clients.add(self)

    def on_message(self, message):
        try:
            data = json.loads(message)
            
            if 'event' in data:
                if data['event'] == 'start':
                    print("Streaming started")
                    self.audio_data = []
                elif data['event'] == 'stop':
                    print("Streaming stopped")
                    self.save_audio_file()
                elif data['event'] == 'audio':
                    audio_data = base64.b64decode(data['data'])
                    self.audio_data.append(audio_data)
                    self.process_audio(audio_data)
        except json.JSONDecodeError:
            print("Received invalid JSON")
        except Exception as e:
            print(f"Error processing message: {str(e)}")

    def on_close(self):
        print("WebSocket closed")
        AudioStreamHandler.clients.remove(self)

    def process_audio(self, audio_data):
        print(f"Received {len(audio_data)} bytes of audio data")

    def save_audio_file(self):
        if not self.audio_data:
            print("No audio data to save")
            return

        filename = f"recorded_audio_{len(os.listdir('recordings')) + 1}.wav"
        with wave.open(f"recordings/{filename}", "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(b''.join(self.audio_data))
        print(f"Audio saved as {filename}")

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        print("MainHandler accessed")
        try:
            self.render("audio_client.html")
        except Exception as e:
            print(f"Error rendering template: {str(e)}")
            self.write("Error rendering template. Check server logs.")

class DebugHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Debug route is working")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/ws", AudioStreamHandler),
        (r"/debug", DebugHandler),
    ], 
    template_path=os.path.dirname(__file__),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    debug=True)

if __name__ == "__main__":
    if not os.path.exists("recordings"):
        os.makedirs("recordings")
    app = make_app()
    app.listen(8888)
    print("Server started on http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()