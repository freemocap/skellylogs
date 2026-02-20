# skellylogs

Opinionated logging configuration for the [FreeMoCap](https://github.com/freemocap) ecosystem.

Provides colorized console output with per-process/per-thread color hashing, delta-time between log entries, custom log levels (`LOOP`, `TRACE`, `SUCCESS`, `API`), a file handler, and a websocket queue handler for forwarding structured log records to a frontend.

## Install

```bash
pip install skellylogs
```

## Quick Start

```python
from skellylogs import configure_logging, LogLevels

configure_logging(level=LogLevels.DEBUG)
```

That's it. Every `logging.getLogger(...)` in your application will now produce colorized, timestamped output to `stdout` and a log file under `~/skellylogs_data/logs/`.

## Custom Log Levels

`skellylogs` registers four custom log levels on every `logging.Logger` instance:

| Method            | Level | Use case                                  |
|-------------------|-------|-------------------------------------------|
| `logger.loop()`   | 3     | Logs inside hot loops (debug only)        |
| `logger.trace()`  | 5     | Low-level tracing for deep debugging      |
| `logger.success()`| 22    | Something worked!                         |
| `logger.api()`    | 25    | API call/response logging                 |

```python
import logging
from skellylogs import configure_logging, LogLevels

configure_logging(level=LogLevels.TRACE)

logger = logging.getLogger(__name__)

logger.trace("About to do the thing")
logger.info("Doing the thing")
logger.success("The thing worked")
logger.api("POST /api/thing -> 200")
logger.loop("This fires every frame, you probably want LOOP level to suppress it")
```

## Suppressing Noisy Packages

By default, `skellylogs` quiets common noisy third-party loggers (`matplotlib`, `httpx`, `uvicorn`, `asyncio`, etc.). This is configurable via the `suppress_packages` parameter — a dict mapping logger names to log levels.

```python
from skellylogs import configure_logging, LogLevels
from skellylogs.package_log_quieters import DEFAULT_NOISY_PACKAGES

# Use the defaults (same as passing None)
configure_logging(level=LogLevels.DEBUG)

# Extend the defaults with app-specific suppressions
configure_logging(
    level=LogLevels.DEBUG,
    suppress_packages=DEFAULT_NOISY_PACKAGES | {"cv2": logging.WARNING, "mediapipe": logging.WARNING},
)

# Completely replace the defaults
configure_logging(
    level=LogLevels.DEBUG,
    suppress_packages={"cv2": logging.WARNING},
)

# Suppress nothing
configure_logging(
    level=LogLevels.DEBUG,
    suppress_packages={},
)
```

The default suppressed packages are:

| Logger        | Level   |
|---------------|---------|
| `tzlocal`     | WARNING |
| `matplotlib`  | WARNING |
| `httpx`       | WARNING |
| `asyncio`     | WARNING |
| `websockets`  | INFO    |
| `websocket`   | INFO    |
| `watchfiles`  | WARNING |
| `httpcore`    | WARNING |
| `urllib3`     | WARNING |
| `comtypes`    | WARNING |
| `uvicorn`     | WARNING |

## Log File Location

By default, log files are written to `~/skellylogs_data/logs/` with ISO-8601 timestamped filenames. To customize this, pass a `log_file_path`:

```python
configure_logging(level=LogLevels.DEBUG, log_file_path="/tmp/my_app.log")
```

## Websocket Log Queue

For applications with a frontend (e.g. FastAPI + websocket), `configure_logging` creates a `multiprocessing.Queue` that receives serialized log records as dicts. You can drain this queue from a websocket endpoint:

```python
from skellylogs import configure_logging, LogLevels
from skellylogs.handlers.websocket_log_queue_handler import get_websocket_log_queue

configure_logging(level=LogLevels.DEBUG)

queue = get_websocket_log_queue()

# In your websocket handler:
while True:
    log_record: dict = queue.get()  # blocks until a log arrives
    await websocket.send_json(log_record)
```

Each dict in the queue follows the `LogRecordModel` schema (a Pydantic model) with fields like `levelname`, `message`, `formatted_message`, `delta_t`, `pathname`, `lineno`, etc.

### Passing the queue to subprocesses

In multiprocessing applications, pass the queue to child processes so their logs also go to the websocket:

```python
import multiprocessing
from skellylogs import configure_logging, LogLevels
from skellylogs.handlers.websocket_log_queue_handler import get_websocket_log_queue

configure_logging(level=LogLevels.DEBUG)
queue = get_websocket_log_queue()

def worker(log_queue: multiprocessing.Queue) -> None:
    configure_logging(level=LogLevels.DEBUG, ws_queue=log_queue)
    # ... do work, all logging goes through the shared queue

process = multiprocessing.Process(target=worker, args=(queue,))
process.start()
```

## What the Output Looks Like

```
└>> Starting camera capture | INFO | 12.450ms | myapp.camera.start():42 | 2025-02-20T14:30:01.123 | PID:12345:MainProcess | TID:67890:MainThread
└>> Frame grabbed in 16ms | TRACE | 0.320ms | myapp.camera.grab():87 | 2025-02-20T14:30:01.139 | PID:12345:MainProcess | TID:67891:FrameThread
```

Each line includes: message, level, delta-time since last log, source location, timestamp, and process/thread info. In the terminal, each level gets its own color, and PID/TID get consistent hashed ANSI colors so you can visually distinguish processes at a glance.

## `configure_logging` API Reference

```python
def configure_logging(
    level: LogLevels,
    ws_queue: multiprocessing.Queue | None = None,
    log_file_path: str | None = None,
    suppress_packages: dict[str, int] | None = None,
) -> None:
```

| Parameter          | Type                          | Default                       | Description |
|--------------------|-------------------------------|-------------------------------|-------------|
| `level`            | `LogLevels`                   | *(required)*                  | Minimum log level for console and websocket handlers |
| `ws_queue`         | `multiprocessing.Queue \| None` | `None`                      | Queue for websocket log distribution. `None` = auto-create in main process |
| `log_file_path`    | `str \| None`                 | `None`                        | Log file path. `None` = `~/skellylogs_data/logs/<timestamp>.log` |
| `suppress_packages`| `dict[str, int] \| None`      | `None` (uses `DEFAULT_NOISY_PACKAGES`) | Third-party logger suppression map. `{}` = suppress nothing |

## Migration from Inline Logging Configuration

If you're currently using the `system/logging_configuration` module from `freemocap` or `skellycam`:

1. `pip install skellylogs`
2. Delete your `system/logging_configuration/` directory
3. Replace imports:
   ```python
   # Before
   from myapp.system.logging_configuration.configure_logging import configure_logging
   from myapp.system.logging_configuration.log_levels import LogLevels

   # After
   from skellylogs import configure_logging, LogLevels
   ```
4. If your `logger_builder.py` imported `get_log_file_path` from your app's `default_paths` module, you now pass the path directly:
   ```python
   from myapp.system.default_paths import get_log_file_path

   configure_logging(level=LogLevels.DEBUG, log_file_path=get_log_file_path())
   ```

The websocket queue imports change similarly:
```python
# Before
from myapp.system.logging_configuration.handlers.websocket_log_queue_handler import (
    get_websocket_log_queue,
    LogRecordModel,
)

# After
from skellylogs.handlers.websocket_log_queue_handler import (
    get_websocket_log_queue,
    LogRecordModel,
)
```

## Dependencies

- `pydantic` (for `LogRecordModel` serialization in the websocket handler)

## License

AGPLv3+
