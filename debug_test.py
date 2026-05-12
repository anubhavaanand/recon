import logging
import asyncio
import sys

# Configure logging to stderr
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)

# Also log to file
file_handler = logging.FileHandler('/tmp/recon_debug.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)

# Now import and run the app
from cli.main import app
if __name__ == "__main__":
    app()
