import argparse
import logging

from flask import Flask
from gevent.pywsgi import WSGIServer
from library.logger import setup_logging

from api.book.bookrix import bookrix
from api.book.gutenberg import gutenberg
from api.book.isbn_perpusnas import isbn_perpusnas
from api.book.manybooks import manybooks
from api.book.journalsplos import journalsplos
from api.book.hathitrust import hathitrust
from api.book.librarybpk import librarybpk
from api.book.ebooksdirectory import ebooksdirectory
from api.book.freetechbooks import freetechbooks
from api.book.pdfdrive import pdfdrive
from api.book.wikibooks import wikibooks

setup_logging()
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    argp = argparse.ArgumentParser(description="API")
    argp.add_argument(
        "-p", "--port", dest="port", help="engine port listened", type=int, default=8000
    )
    argp.add_argument("-apps", "--apps", dest="apps", help="apps listened")

    args = argp.parse_args()

    from api import sdk

    class App(Flask):
        def __init__(self, import_name, **kwargs):
            super().__init__(import_name)

    app = App(__name__)
    app.register_blueprint(sdk)
    application = app

    logger.info(f"listening to http://0.0.0.0:{args.port}")
    http_server = WSGIServer(("0.0.0.0", args.port), application, log=logger)
    http_server.serve_forever()
