# Simplified logging module
import logging

def configure_logging():
    """Configure basic logging for development"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def get_logger(name):
    """Get a logger instance"""
    return logging.getLogger(name)

# Create standard loggers
audit_logger = get_logger('audit')
security_logger = get_logger('security')
performance_logger = get_logger('performance')
app_logger = get_logger('app')

__all__ = [
    'configure_logging',
    'get_logger',
    'audit_logger',
    'security_logger',
    'performance_logger',
    'app_logger'
]