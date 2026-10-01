import logging
import sys
from pythonjsonlogger import jsonlogger
import contextvars

# We will read this from the middleware
correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Inject correlation_id dynamically
    class CorrelationIdFilter(logging.Filter):
        def filter(self, record):
            record.correlation_id = correlation_id.get()
            return True
            
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(correlation_id)s %(message)s"
    )

    # Don't remove pytest handlers, just add or update
    has_stream = False
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not type(handler).__name__.startswith('_'):
            handler.setFormatter(formatter)
            handler.addFilter(CorrelationIdFilter())
            has_stream = True
            
    if not has_stream:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        handler.addFilter(CorrelationIdFilter())
        logger.addHandler(handler)
