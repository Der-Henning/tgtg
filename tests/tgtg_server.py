import argparse
import json
import logging
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urljoin

import requests

from tgtg_scanner.tgtg.tgtg_client import API_ITEM_ENDPOINT, BASE_URL

FAVORITES = []


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n",
                     str(self.path), str(self.headers))
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("<h1>TGTG API test server</h1>".encode('utf-8'))
        self.wfile.write(f"GET request for {self.path}".encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\nBody:\n%s\n",
                     str(self.path),
                     str(self.headers),
                     post_data.decode('utf-8'))

        path = self.path[1:]
        headers = self.headers
        headers["Host"] = "apptoogoodtogo.com"
        url = urljoin(BASE_URL, path)
        response = requests.post(url, post_data, headers=headers)

        response_data = response.content
        if path == API_ITEM_ENDPOINT:
            response_json = response.json()
            for i in range(len(response_json.get("items"))):
                new_avail = random.randint(0, 3)
                response_json["items"][i]["items_available"] = new_avail
            response_data = json.dumps(response_json).encode("utf-8")

        logging.debug("POST response,\nBody:\n%s\n", response_data)
        self.send_response(response.status_code)
        self.send_header("Set-Cookie",
                         f"datadome={response.cookies.get('datadome')}; "
                         f"Domain=.local; Path=/")
        self.end_headers()
        self.wfile.write(response_data)


def run_server(port: int = 8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, RequestHandler)
    logging.info('Starting httpd...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...')


def main():
    parser = argparse.ArgumentParser(description="TGTG API test server")
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="activate debugging mode")
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8080
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    run_server(args.port)


if __name__ == "__main__":
    main()
