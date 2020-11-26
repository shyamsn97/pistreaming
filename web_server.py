import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server
import numpy as np
import cv2
from yolov3 import YoloRunner
import click

PAGE="""\
<html>
<head>
<title>picamera MJPEG streaming demo</title>
</head>
<body>
<h1>PiCamera MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="640" height="480" />
</body>
</html>
"""

@click.command()
@click.option('--weight_path')
@click.option('--model_config')
@click.option('--class_names', default="person")
@click.option('--draw', default=False)
def main(weight_path, model_config, class_names, draw):
    print("making net...")
    net = YoloRunner(weight_path=weight_path, model_config=model_config, class_names=["person"])
    print('Initializing camera')
    
    class StreamingOutput(object):
        def __init__(self):
            self.frame = None
            self.buffer = io.BytesIO()
            self.condition = Condition()

        def write(self, buf):
            if buf.startswith(b'\xff\xd8'):
                # New frame, copy the existing buffer's content and notify all
                # clients it's available
                self.buffer.truncate()
                with self.condition:
                    self.frame = self.buffer.getvalue()
                    self.condition.notify_all()
                self.buffer.seek(0)
            return self.buffer.write(buf)

    class StreamingHandler(server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(301)
                self.send_header('Location', '/index.html')
                self.end_headers()
            elif self.path == '/index.html':
                content = PAGE.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Content-Length', len(content))
                self.end_headers()
                self.wfile.write(content)
            elif self.path == '/stream.mjpg':
                self.send_response(200)
                self.send_header('Age', 0)
                self.send_header('Cache-Control', 'no-cache, private')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
                self.end_headers()
                try:
                    while True:
                        with output.condition:
                            output.condition.wait()
                            frame = output.frame
                            bytes_as_np_array = np.frombuffer(frame, dtype=np.uint8)
                            rgb = cv2.imdecode(bytes_as_np_array,cv2.IMREAD_UNCHANGED)
                            out = net.inference(rgb)[0]
                            net.draw_boxes(rgb, out[0], class_idx=out[2], class_prob=out[1])
                            frame = cv2.imencode('.jpg', rgb)[1]
                        self.wfile.write(b'--FRAME\r\n')
                        self.send_header('Content-Type', 'image/jpeg')
                        self.send_header('Content-Length', len(frame))
                        self.end_headers()
                        self.wfile.write(frame)
                        self.wfile.write(b'\r\n')
                except Exception as e:
                    logging.warning(
                        'Removed streaming client %s: %s',
                        self.client_address, str(e))
            else:
                self.send_error(404)
                self.end_headers()

    class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
        allow_reuse_address = True
        daemon_threads = True

    with picamera.PiCamera(resolution='640x480', framerate=2) as camera:
        output = StreamingOutput()
        camera.start_recording(output, format='mjpeg')
        try:
            address = ('', 8000)
            main_server = StreamingServer(address, StreamingHandler)
            main_server.serve_forever()
        finally:
            camera.stop_recording()

if __name__ == '__main__':
    main()