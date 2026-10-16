"""Run the development CLI with browser URLs for Docker's published port."""

import logging
import os

from flask.cli import main


class BrowserAddressFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        # Werkzeug includes container addresses in its startup log record.
        # Replace only those lines; preserve warnings and request/error logs.
        if "Running on http://" in message:
            lines = [line for line in message.splitlines() if "Running on http://" not in line]
            lines.append(f" * Browser: {os.environ['DEV_BROWSER_URL']}/api/health")
            record.msg = "\n".join(lines)
            record.args = ()
        return True


if __name__ == "__main__":
    if os.environ.get("DEV_BROWSER_URL"):
        logging.getLogger("werkzeug").addFilter(BrowserAddressFilter())
    main()
