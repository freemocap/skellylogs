import logging

DEFAULT_NOISY_PACKAGES: dict[str, int] = {
    "tzlocal": logging.WARNING,
    "matplotlib": logging.WARNING,
    "httpx": logging.WARNING,
    "asyncio": logging.WARNING,
    "websockets": logging.INFO,
    "websocket": logging.INFO,
    "watchfiles": logging.WARNING,
    "httpcore": logging.WARNING,
    "urllib3": logging.WARNING,
    "comtypes": logging.WARNING,
    "uvicorn": logging.WARNING,
}


def suppress_noisy_package_logs(packages: dict[str, int]) -> None:
    """Set log levels on noisy third-party loggers.

    Args:
        packages: Map of {logger_name: level} to apply.
    """
    for name, level in packages.items():
        logging.getLogger(name).setLevel(level)
