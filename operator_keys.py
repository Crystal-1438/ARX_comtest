"""Local operator keys, the arm/stop channel the leader wire format lacks.

The leader board reports positions and nothing else: no arm, no stop, no
deadman. Without a local channel an operator could arm once and then have no
way back from a latched fault. This reads single keys from stdin without a
thread, so the control loop keeps its own timing.

Named operator_keys rather than operator: this directory is sys.path[0] when
app.py runs, and shadowing the stdlib operator module breaks collections.
"""

import os
import select
import sys

ARM_KEYS = frozenset("aA")
STOP_KEYS = frozenset("sS ")


class NullInput:
    """Stand-in when local keys are not requested."""

    def poll(self):
        return []

    def close(self):
        pass


class KeyInput:
    """poll() -> list[str] of "arm"/"stop", oldest first, never blocking."""

    def __init__(self, stream=None):
        self.stream = sys.stdin if stream is None else stream
        self.saved = None
        self.exhausted = False
        try:
            self.fd = self.stream.fileno()
        except (AttributeError, ValueError, OSError):
            self.fd = None
        if self.fd is not None and os.isatty(self.fd):
            self._cbreak()

    def _cbreak(self):
        import termios
        import tty
        self.saved = termios.tcgetattr(self.fd)
        # cbreak rather than raw: ISIG stays on, so Ctrl-C still reaches the
        # existing signal handler instead of arriving as a byte we ignore.
        tty.setcbreak(self.fd)

    def poll(self):
        if self.fd is None or self.exhausted:
            return []
        try:
            if not select.select([self.fd], [], [], 0)[0]:
                return []
            chunk = os.read(self.fd, 64)
        except (BlockingIOError, InterruptedError):
            return []
        except (OSError, ValueError):
            self.exhausted = True
            return []
        if not chunk:
            self.exhausted = True  # Closed stdin is not an ongoing source of keys.
            return []
        actions = []
        for character in chunk.decode("utf-8", "replace"):
            if character in ARM_KEYS:
                actions.append("arm")
            elif character in STOP_KEYS:
                actions.append("stop")
        return actions

    def close(self):
        if self.saved is None or self.fd is None:
            return
        import termios
        try:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.saved)
        except (OSError, ValueError, termios.error):
            pass
        finally:
            self.saved = None
