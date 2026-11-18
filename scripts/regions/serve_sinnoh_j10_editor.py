#!/usr/bin/env python3
"""Serve ONLY the static J10 authoring editor on loopback (no upload endpoint)."""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import sys
import webbrowser

ROOT=Path(__file__).resolve().parents[2]
HTML=ROOT/"web/sinnoh-j10-map-editor.html"
URL="http://127.0.0.1:8772/sinnoh-j10-map-editor.html"

class J10Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/sinnoh-j10-map-editor.html", "/"):
            self.send_error(404,"J10 serves only the editor")
            return
        if HTML.is_symlink() or not HTML.is_file():
            self.send_error(503,"Editor not found")
            return
        raw=HTML.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(raw)))
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; script-src 'unsafe-inline'; "
                         "style-src 'unsafe-inline'; img-src blob: data:; "
                         "connect-src 'none'; form-action 'none'; frame-ancestors 'none'")
        self.send_header("X-Content-Type-Options","nosniff")
        self.end_headers()
        self.wfile.write(raw)
    def do_POST(self):
        self.send_error(405,"No uploads accepted")
    def log_message(self,fmt,*args):
        pass

def main():
    if not HTML.is_file():
        print("SINNOH_J10_BLOQUEADO:editor HTML ausente",file=sys.stderr)
        return 2
    try:
        server=ThreadingHTTPServer(("127.0.0.1",8772),J10Handler)
    except OSError as exc:
        print("SINNOH_J10_BLOQUEADO:porta local indisponível: "+str(exc),file=sys.stderr)
        return 2
    print("Editor local J10 em "+URL,flush=True)
    webbrowser.open(URL)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
    return 0

if __name__=="__main__":
    raise SystemExit(main())
