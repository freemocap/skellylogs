# Logging lifecycle investigation — 2026-09-28

## What this change fixes

Repeated configuration closes replaced handlers, retains only one traceback
filter, and registers one owned-queue cleanup callback. Explicit
`configure_logging(..., use_websocket=False)` retains console/file/custom-level
logging without constructing a multiprocessing queue. This mode already existed;
tests now protect it, including in a child process. Queue ownership and the
existing multiprocessing relay remain unchanged.

SkellyLogs does not start a relay process. Its multiprocessing queue starts a
feeder **thread** when records are enqueued. Its pipe and synchronization resources
can still be unavailable in restricted execution environments. Applications must
choose console/file-only mode explicitly when a relay is unnecessary. Do not
silently disable an application-required relay after an IPC failure.

## Unresolved shutdown failure — consumer integration required

`python -B tests/diagnose_undrained_queue.py` writes one large log record without
a consumer. On this Windows checkout it reports:

    Shutdown hung after body completed: True

The diagnostic kills its disposable child after five seconds. The current
`configure_logging._cleanup_log_queue` calls `close()` then `join_thread()`;
the feeder cannot finish when nobody drains the pipe. This patch does NOT fix
that failure. Child producers also have multiprocessing's normal exit-time
feeder joining. Replacing the queue with a thread-only queue would break spawned
worker logging. Cancelling feeder joins is not an acceptable general fix: a
producer exiting mid-write can leave the shared pipe/lock unusable for others.

In FreeMoCap:

- `freemocap/api/websocket/websocket_server.py::_logs_relay` consumes the shared
  queue only while that websocket connection remains active. It stops on socket
  shutdown. Multiple connections also compete for the same records rather than
  receiving a broadcast.
- `freemocap/core/pipeline/abcs/pipeline_ipc.py::PipelineIPC.create` obtains the
  queue; posthoc/realtime workers receive it.
- Spawned worker setup is in SkellyCam
  `skellycam/core/ipc/process_management/managed_worker.py`, which calls
  `configure_logging(..., ws_queue=log_queue)` inside the worker entry point.

The next separately reviewed core stage should create one application-owned
continuous queue consumer, independent of websocket client lifetime. It drains
while workers exist, broadcasts to clients through bounded per-client buffers,
and drops only relay copies when no client exists or a client is slow. Shutdown
must stop/join producers while this consumer still drains, then stop the consumer
and close the queue. Console/file records continue through their normal handlers;
frontend delivery is best effort and is not durable storage. Core tests should
cover no client, disconnect/reconnect, slow clients, multiple clients, and worker
exit under sustained logging. Do not introduce a second competing queue reader.

## Validation and remaining integration

- `uv sync --group test` installed the existing declared test group.
- `python -B -m pytest -q`: 83 passed, including spawned producer delivery/exit,
  no-IPC console/file mode, handler closure, and externally owned queue retention.
- Main branch is clean before this change and matches cached origin/HEAD. Core
  has no explicit SkellyLogs branch pin. Live remote verification was unavailable.
- Root logger's configured level filters records before handler thresholds;
  a TRACE file-handler threshold does not override an INFO root threshold.
- Forge dependency restoration/bootstrap and fitting progress logs remain a
  separate downstream stage after the human commits/pushes this repository.

Current source installation is `pip install .` from this checkout, or the
project's declared Git source. Public-index availability must be verified before
documenting `pip install skellylogs` as an available distribution route.
