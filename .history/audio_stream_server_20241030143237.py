import tornado.ioloop
import tornado.web
import tornado.websocket
import json
import wave
import os
import numpy as np

SAMPLE_RATE = 44100  # Standard sample rate

class AudioStreamHandler(tornado.websocket.WebSocketHandler):
    clients = set()
    audio_data = []

    def check_origin(self, origin):
        return True

    def open(self):
        print("WebSocket opened")
        self.clients.add(self)

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
                    audio_data = np.frombuffer(bytes(data['data']), dtype=np.float32)
                    self.audio_data.append(audio_data)
                    print(f"Received audio chunk. Shape: {audio_data.shape}, Min: {audio_data.min()}, Max: {audio_data.max()}")
        except json.JSONDecodeError:
            print("Received invalid JSON")
        except Exception as e:
            print(f"Error processing message: {str(e)}")

    def on_close(self):
        print("WebSocket closed")
        self.clients.remove(self)

    def save_audio_file(self):
        if not self.audio_data:
            print("No audio data to save")
            return

        filename = f"recorded_audio_{len(os.listdir('recordings')) + 1}.wav"
        audio_data = np.concatenate(self.audio_data)
        
        # Convert float32 to int16
        audio_data_int = (audio_data * 32767).astype(np.int16)
        
        with wave.open(f"recordings/{filename}", "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 2 bytes for int16
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data_int.tobytes())
        print(f"Audio saved as {filename}")

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