# SkellyLogs agent guidance

SkellyLogs owns reusable logging configuration, handlers and queue behavior;
application integration and relay orchestration belong to the consumer. Keep
the package independently usable rather than importing consuming applications.

At milestones, checkpoint the objective, decisions and rationale, exact checkout,
existing interfaces, validation results and next action with targeted reading
paths. After compaction or handoff, read the checkpoint, relevant portions of
[README.md](README.md), [logging lifecycle findings](notes/LOGGING_LIFECYCLE_HANDOFF.md),
and the affected code/diff under `skellylogs/` before editing. The lifecycle note
distinguishes handler/queue ownership from consumer relay shutdown; verify its
dated findings before treating them as current failures or completed fixes.

Search existing handlers and configuration before adding replacement lifecycle
logic. Continue authorized work when the next action's purpose and owner are
clear; ask only for consequential intent unresolved by inspection. Follow
workspace policy when present, preserve existing edits, follow the workspace Git authorization and repository-scope policy, and verify output paths are ignored or external before diagnostics.
