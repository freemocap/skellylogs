"""Configuration lifecycle: local logging never requires IPC resources."""
import importlib
import logging
import subprocess
import sys
from types import SimpleNamespace

from skellylogs import LogLevels, configure_logging
from skellylogs.filters.stringify_traceback import StringifyTracebackFilter
from skellylogs.handlers.websocket_log_queue_handler import WebSocketQueueHandler

configuration = importlib.import_module("skellylogs.configure_logging")


def test_console_file_mode_does_not_construct_queue(monkeypatch, tmp_path):
    def forbidden_queue():
        raise AssertionError("Console/file mode must not allocate IPC")

    monkeypatch.setattr(configuration, "create_websocket_log_queue", forbidden_queue)
    path = tmp_path / "local.log"
    configure_logging(LogLevels.DEBUG, log_file_path=str(path), use_websocket=False)
    logging.getLogger("standalone.solver").info("local logging works")
    assert "local logging works" in path.read_text()
    assert not any(isinstance(h, WebSocketQueueHandler) for h in logging.getLogger().handlers)


def test_child_explicit_console_file_mode_keeps_local_logging(monkeypatch, tmp_path):
    monkeypatch.setattr(configuration.multiprocessing, "current_process",
                        lambda: SimpleNamespace(name="SpawnProcess-1"))
    path = tmp_path / "child.log"
    configure_logging(LogLevels.DEBUG, log_file_path=str(path), use_websocket=False)
    logging.getLogger("child.solver").warning("child local record")
    assert "child local record" in path.read_text()
    assert not any(isinstance(h, WebSocketQueueHandler) for h in logging.getLogger().handlers)


def test_reconfigure_closes_old_file_and_does_not_duplicate_filter(tmp_path):
    configure_logging(LogLevels.DEBUG, log_file_path=str(tmp_path / "first.log"), use_websocket=False)
    root = logging.getLogger()
    previous = next(h for h in root.handlers if isinstance(h, logging.FileHandler))
    configure_logging(LogLevels.DEBUG, log_file_path=str(tmp_path / "second.log"), use_websocket=False)
    assert previous.stream is None
    assert sum(isinstance(f, StringifyTracebackFilter) for f in root.filters) == 1


def test_disabling_relay_does_not_close_external_queue(tmp_path):
    class ExternalQueue:
        def __init__(self):
            self.records = []

        def put_nowait(self, record):
            self.records.append(record)

        def close(self):
            raise AssertionError("Externally owned queue must remain usable")

    queue = ExternalQueue()
    configure_logging(LogLevels.DEBUG, ws_queue=queue, log_file_path=str(tmp_path / "relay.log"))
    logging.getLogger("relay").info("forwarded")
    configure_logging(LogLevels.DEBUG, log_file_path=str(tmp_path / "local.log"), use_websocket=False)
    logging.getLogger("relay").info("local only")
    assert [r["message"] for r in queue.records] == ["forwarded"]


def test_spawned_producer_relay_delivery_and_exit(tmp_path):
    script = tmp_path / "producer.py"
    script.write_text('''
import multiprocessing
from skellylogs import configure_logging, LogLevels
import logging
import sys

def produce(queue, path):
    configure_logging(LogLevels.INFO, ws_queue=queue, log_file_path=path)
    logging.getLogger("worker").info("child relay record")

if __name__ == "__main__":
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=produce, args=(queue, sys.argv[1]))
    process.start()
    try:
        assert queue.get(timeout=10)["message"] == "child relay record"
        process.join(timeout=10)
        assert process.exitcode == 0
    finally:
        if process.is_alive():
            process.terminate()
            process.join()
        queue.close()
        queue.join_thread()
''')
    subprocess.run([sys.executable, "-B", str(script), str(tmp_path / "child.log")],
                   check=True, timeout=20, capture_output=True)
