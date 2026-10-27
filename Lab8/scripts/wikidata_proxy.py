# -*- coding: utf-8 -*-
"""Мінімальний SPARQL-проксі до Wikidata з обов’язковим User-Agent.

Потрібен тому, що Wikidata повертає 403 для HTTP-клієнта Jena без
User-Agent. Проксі лише додає заголовок і передає запит до Wikidata.
"""
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import requests

UPSTREAM = "https://query.wikidata.org/sparql"
UA = "KnowledgeStorageLab/1.0 (educational; Lviv University; contact: student)"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path not in ("/sparql", "/"):
            self.send_error(404)
            return
        query = parse_qs(parsed.query).get("query", [""])[0]
        self._forward(query)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path not in ("/sparql", "/"):
            self.send_error(404)
            return
        n = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(n).decode("utf-8", "replace")
        ctype = self.headers.get("Content-Type", "")
        if "application/sparql-query" in ctype:
            query = body
        else:
            query = parse_qs(body).get("query", [""])[0]
        self._forward(query)

    def _forward(self, query):
        if not query:
            self.send_error(400, "missing query")
            return
        accept = self.headers.get("Accept", "application/sparql-results+json")
        try:
            r = requests.get(UPSTREAM, params={"query": query},
                             headers={"Accept": accept, "User-Agent": UA},
                             timeout=90)
        except Exception as e:
            self.send_error(502, str(e))
            return
        self.send_response(r.status_code)
        self.send_header("Content-Type", r.headers.get("Content-Type", "application/sparql-results+json"))
        self.send_header("Content-Length", str(len(r.content)))
        self.end_headers()
        self.wfile.write(r.content)

    def log_message(self, fmt, *args):
        sys.stderr.write("[proxy] " + fmt % args + "\n")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3031
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Wikidata proxy on http://127.0.0.1:{port}/sparql", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
