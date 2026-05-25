"""Local HTTP API used for deterministic CI integration tests."""

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class LocalTestApiHandler(BaseHTTPRequestHandler):
    """HTTP handler that mimics a small subset of httpbin-style endpoints."""

    server_version = "LocalTestApi/1.0"
    flaky_counters = {}
    flaky_lock = threading.Lock()

    def log_message(self, format, *args):  # noqa: A003
        # Keep logs compact in CI while still emitting useful diagnostics.
        super().log_message(format, *args)

    def _read_body(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return "", None

        raw = self.rfile.read(content_length)
        text = raw.decode("utf-8", errors="replace")

        try:
            parsed_json = json.loads(text)
        except json.JSONDecodeError:
            parsed_json = None

        return text, parsed_json

    def _write_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _request_payload(self, method):
        parsed = urlparse(self.path)
        text_body, json_body = self._read_body()
        return {
            "method": method,
            "path": parsed.path,
            "query": parse_qs(parsed.query),
            "headers": {k: v for k, v in self.headers.items()},
            "body": text_body,
            "json": json_body,
            "url": self.path,
        }

    def _first_query_value(self, parsed, key, default=None):
        values = parse_qs(parsed.query).get(key)
        if not values:
            return default
        return values[0]

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            self._write_json(200, {"ok": True})
            return

        if path == "/get":
            self._write_json(200, self._request_payload("GET"))
            return

        if path.startswith("/delay/"):
            try:
                seconds = float(path.split("/", 2)[2])
            except (ValueError, IndexError):
                self._write_json(400, {"error": "invalid delay"})
                return

            time.sleep(max(0.0, min(seconds, 5.0)))
            self._write_json(200, self._request_payload("GET"))
            return

        if path.startswith("/status/"):
            try:
                code = int(path.split("/", 2)[2])
            except (ValueError, IndexError):
                self._write_json(400, {"error": "invalid status code"})
                return

            self._write_json(code, self._request_payload("GET"))
            return

        if path.startswith("/flaky/"):
            key = path.split("/", 2)[2] if len(path.split("/", 2)) > 2 else "default"
            try:
                failures = int(self._first_query_value(parsed, "failures", "2"))
                fail_status = int(self._first_query_value(parsed, "status", "429"))
                success_status = int(self._first_query_value(parsed, "success_status", "200"))
            except ValueError:
                self._write_json(400, {"error": "invalid flaky endpoint query"})
                return

            with self.flaky_lock:
                current_attempt = self.flaky_counters.get(key, 0) + 1
                self.flaky_counters[key] = current_attempt

            payload = self._request_payload("GET")
            payload["attempt"] = current_attempt
            payload["failures"] = failures

            if current_attempt <= failures:
                self._write_json(fail_status, payload)
            else:
                self._write_json(success_status, payload)
            return

        self._write_json(404, {"error": "not found", "path": path})

    def do_POST(self):  # noqa: N802
        self._write_json(200, self._request_payload("POST"))

    def do_PUT(self):  # noqa: N802
        self._write_json(200, self._request_payload("PUT"))

    def do_DELETE(self):  # noqa: N802
        self._write_json(200, self._request_payload("DELETE"))

    def do_PATCH(self):  # noqa: N802
        self._write_json(200, self._request_payload("PATCH"))

    def do_HEAD(self):  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_OPTIONS(self):  # noqa: N802
        payload = {
            "allowed_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
            "path": urlparse(self.path).path,
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Allow", "GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description="Run the local test API server")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=18080, help="Port to listen on")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), LocalTestApiHandler)
    print(f"Local test API listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
