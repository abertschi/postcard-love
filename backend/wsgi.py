from backend import app
from flask import request
import logging


class RequestFormatter(logging.Formatter):
    def format(self, record):
        record.url = request.url if request else '-'
        record.remote_addr = request.remote_addr if request else '-'
        record.request_id = request.environ.get("FLASK_REQUEST_ID") if request else '-'
        return super().format(record)


if __name__ == "__main__":
    formatter = RequestFormatter(
        '%(asctime)s.%(msecs)03d %(levelname)s %(module)s %(funcName)s '
        '%(request_id)s %(remote_addr)s %(url)s %(message)s'
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO,
                        handlers=[ch],
                        datefmt="%Y-%m-%d %H:%M:%S")
    app.run()
