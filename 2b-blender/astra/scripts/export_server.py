"""One local export endpoint for the procedural browser generator. No uploads leave the PC."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT),**kw)
    def do_POST(self):
        if self.path!='/export': self.send_error(404); return
        length=int(self.headers.get('Content-Length',0))
        if not 0<length<20000000: self.send_error(413); return
        data=self.rfile.read(length); parsed=json.loads(data)
        assert parsed['schema']==1 and len(parsed['motion'])==240
        (ROOT/'diorama.json').write_bytes(data)
        self.send_response(200); self.end_headers(); self.wfile.write(b'Exported')
        print('EXPORTED',len(data),'bytes',flush=True)
if __name__=='__main__': ThreadingHTTPServer(('127.0.0.1',8083),Handler).serve_forever()
