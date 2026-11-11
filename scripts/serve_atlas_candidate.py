"""Serve the audited static candidate for local checks, optionally shaping responses."""
import argparse
import gzip
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from mimetypes import guess_type
from pathlib import Path
from threading import Lock
from time import sleep
from urllib.parse import urlsplit

from package_atlas_static import HEADERS, ROOT, verify_folder

OUT = ROOT/'output/atlas'
NETWORK_PROFILE = {'downstreamBitsPerSecond': 20_000_000, 'requestLatencyMs': 100}


def serve(port, shape):
    pointer=json.loads((OUT/'release.json').read_text())
    manifest=OUT/pointer['manifest']
    release=json.loads(manifest.read_text())
    folder=manifest.parent/'static'
    assets=release['static']['assets']
    verify_folder(folder,assets)
    portable=(manifest.parent/release['portable']['path']).read_bytes()
    pace=Lock()
    public_headers=[line.strip().split(': ',1) for line in HEADERS.splitlines() if line.startswith('  ')]
    offline_headers=[(k,v.replace("script-src 'self'","script-src 'unsafe-inline'").replace("connect-src 'self'","connect-src 'none'").replace("img-src 'self'","img-src").replace("font-src 'self'","font-src data:"))
                     for k,v in public_headers]

    class Preview(BaseHTTPRequestHandler):
        def do_GET(self):
            route=urlsplit(self.path).path
            key=route.removeprefix('/') or 'index.html'
            offline=key=='offline/'
            if not offline and (key not in assets or key=='_headers'):
                self.send_error(404)
                return
            payload=portable if offline else (folder/key).read_bytes()
            kind='text/html' if offline else guess_type(key)[0] or 'application/octet-stream'
            if key.endswith('.mjs'):kind='text/javascript'
            zipped=not offline and not key.endswith('.webp') and 'gzip' in self.headers.get('Accept-Encoding','')
            if zipped:payload=gzip.compress(payload,mtime=0)
            if shape:sleep(NETWORK_PROFILE['requestLatencyMs']/1000)
            self.send_response(200)
            self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(payload)))
            self.send_header('Cache-Control','no-store')
            if zipped:self.send_header('Content-Encoding','gzip')
            for header,value in (offline_headers if offline else public_headers):self.send_header(header,value)
            self.end_headers()
            try:
                if shape:
                    for offset in range(0,len(payload),16384):
                        chunk=payload[offset:offset+16384]
                        with pace:
                            sleep(8*len(chunk)/NETWORK_PROFILE['downstreamBitsPerSecond'])
                            self.wfile.write(chunk)
                else:self.wfile.write(payload)
            except (BrokenPipeError,ConnectionResetError):
                pass

    print(f"Serving release {release['releaseId']} at http://127.0.0.1:{port}/",flush=True)
    if shape:print(json.dumps(NETWORK_PROFILE),flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Preview).serve_forever()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8017)
    parser.add_argument('--shape',action='store_true')
    args=parser.parse_args()
    serve(args.port,args.shape)
