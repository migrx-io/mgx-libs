"""
Test HTTP server

Send a GET request::
    curl http://localhost
Send a HEAD request::
    curl -I http://localhost
Send a POST request::
    curl -d "foo=bar&bin=baz" http://localhost

"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import logging as log
import threading
import json


class S(BaseHTTPRequestHandler):

    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.wfile.write(b'{"ok": "ok"}')

    def do_DELETE(self):
        self._set_headers(500)
        self.wfile.write(b'{"error": "error"}')

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        log.debug("do_POST: %s", post_data)
        self._set_headers()
        self.wfile.write(b"ok")

    def do_PUT(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        log.debug("do_PUT: %s", post_data)

        if json.loads(post_data).get("error") == 1:
            raise Exception("error occured")

        self._set_headers()
        self.wfile.write(b"ok")


def run(server_class=HTTPServer, handler_class=S, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    log.debug('Starting httpd...')
    httpd.serve_forever()


def run_test_server(port):
    thread = threading.Thread(target=lambda port: run(port=port),
                              args=(port, ))

    return thread
