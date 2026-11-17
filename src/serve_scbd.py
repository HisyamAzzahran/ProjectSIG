"""Serve only the SCBD outputs on localhost; keep repository and credentials private."""
import argparse
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import webbrowser
from .data_loader import ROOT


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--no-browser',action='store_true');args=parser.parse_args()
    folder=ROOT/'outputs/scbd_jakarta'
    if not (folder/'SCBD_Jakarta_Live.html').is_file():
        raise SystemExit('Generate the study first: python -m src.scbd_case')
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(SimpleHTTPRequestHandler,directory=str(folder)))
    url=f'http://127.0.0.1:{server.server_port}/SCBD_Jakarta_Live.html'
    print(url,flush=True)
    if not args.no_browser:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
