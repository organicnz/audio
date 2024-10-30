import tornado.ioloop
import tornado.web
import tornado.websocket
import json
import base64

class AudioStreamHandler(tornado.websocket.WebSocketHandler):
    clients = set()

    def check_origin(self, origin):
        # Allow connections from any origin
        return True

    def open(self):
        print("WebSocket opened")
        AudioStreamHandler.clients.add(self)

    def on_message(self, message):
        try:
            # Assuming the message is a JSON string
            data = json.loads(message)
            
            if 'event' in data:
                if data['event'] == 'start':
                    print("Streaming started")
                elif data['event'] == 'stop':
                    print("Streaming stopped")
                elif data['event'] == 'audio':
                    # Process audio data
                    audio_data = base64.b64decode(data['data'])
                    self.process_audio(audio_data)
        except json.JSONDecodeError:
            print("Received invalid JSON")
        except Exception as e:
            print(f"Error processing message: {str(e)}")

    def on_close(self):
        print("WebSocket closed")
        AudioStreamHandler.clients.remove(self)

    def process_audio(self, audio_data):
        # Here you can implement your audio processing logic
        # For example, save to file, perform analysis, etc.
        print(f"Received {len(audio_data)} bytes of audio data")

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Audio Streaming Server")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/ws", AudioStreamHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("Server started on port 8888")
    tornado.ioloop.IOLoop.current().start()
