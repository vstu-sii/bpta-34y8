import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            response = {
                "status": "ok",
                "service": "bpta-34y8",
            }
        else:
            response = {
                "message": "Hello, world!",
                "service": "bpta-34y8",
                "status": "running",
            }

        body = json.dumps(response).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)


def main():
    host = "0.0.0.0"
    port = int(os.getenv("PORT", "8000"))

    server = ThreadingHTTPServer((host, port), RequestHandler)

    print(f"Server started on {host}:{port}", flush=True)

    server.serve_forever()


if __name__ == "__main__":
    main()