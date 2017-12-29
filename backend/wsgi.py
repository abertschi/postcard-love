from backend import app
from backend import RequestFormatter
import logging

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
