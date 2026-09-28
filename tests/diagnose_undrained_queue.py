"""Run manually: demonstrate current undrained relay shutdown hang in 5 seconds.

This diagnoses an unresolved consumer lifecycle issue; it is not a passing
behavior requirement. The child is terminated after the deadline.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    code = '''
import logging
from skellylogs import configure_logging, LogLevels
configure_logging(LogLevels.INFO, log_file_path=PATH)
logging.getLogger("diagnostic").info("x" * 100000)
print("BODY_COMPLETE", flush=True)
'''.replace("PATH", repr(str(Path(directory) / "diagnostic.log")))
    process = subprocess.Popen([sys.executable, "-B", "-c", code],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        output, errors = process.communicate(timeout=5)
        print("Exited:", process.returncode, errors.decode(errors="replace"))
    except subprocess.TimeoutExpired:
        process.kill()
        output, errors = process.communicate()
        print("Shutdown hung after body completed:", b"BODY_COMPLETE" in output)
