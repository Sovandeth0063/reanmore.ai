import logging
import sys

# Configure root logging formatter and handlers
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Custom logger instance for the orchestrator app
logger = logging.getLogger("orchestrator")
