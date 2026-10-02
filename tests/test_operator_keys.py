import io
import os
import pty
import unittest

from operator_keys import KeyInput, NullInput


def pipe(payload=b""):
    """A readable stream over a pipe; the caller owns nothing."""
    read, write = os.pipe()
    stream = os.fdopen(read, "rb", buffering=0)
    if payload:
        os.write(write, payload)
    os.close(write)
    return stream


class KeyInputTests(unittest.TestCase):
    def keys(self, payload=b""):
        stream = pipe(payload)
        self.addCleanup(stream.close)
        return KeyInput(stream)

    def terminal(self):
        """A KeyInput on a real pty, with the modes that were in force before it."""
        import termios
        master, slave = pty.openpty()
        stream = os.fdopen(os.dup(slave), "rb", buffering=0)
        self.addCleanup(stream.close)
        self.addCleanup(os.close, slave)
        self.addCleanup(os.close, master)
        before = termios.tcgetattr(slave)
        keys = KeyInput(stream)
        self.addCleanup(keys.close)  # idempotent, so tests may close early
        return master, slave, before, keys

    def test_reads_pipe_input_without_a_tty(self):
        self.assertEqual(self.keys(b"a").poll(), ["arm"])

    def test_returns_every_action_in_the_order_typed(self):
        self.assertEqual(self.keys(b"s a").poll(), ["stop", "stop", "arm"])

    def test_ignores_unrelated_keys(self):
        self.assertEqual(self.keys(b"x\nqQz").poll(), [])

    def test_never_blocks_when_there_is_nothing_to_read(self):
        keys = self.keys()
        for _ in range(3):
            self.assertEqual(keys.poll(), [])

    def test_polling_consumes_each_key_once(self):
        keys = self.keys(b"a")
        self.assertEqual(keys.poll(), ["arm"])
        self.assertEqual(keys.poll(), [])

    def test_closed_stdin_stops_producing_actions(self):
        keys = self.keys()
        self.assertEqual(keys.poll(), [])
        self.assertEqual(keys.poll(), [])

    def test_stream_without_a_fileno_is_inert(self):
        keys = KeyInput(io.StringIO("a"))
        self.assertEqual(keys.poll(), [])
        keys.close()

    def test_cbreak_mode_is_actually_engaged(self):
        import termios
        _, slave, before, _ = self.terminal()
        flags = termios.tcgetattr(slave)[3]
        self.assertTrue(before[3] & termios.ICANON)
        self.assertFalse(flags & (termios.ICANON | termios.ECHO))

    def test_ctrl_c_still_reaches_the_signal_handler(self):
        # cbreak, not raw: ISIG must stay on or the app's SIGINT handler never runs.
        import termios
        _, slave, _, _ = self.terminal()
        self.assertTrue(termios.tcgetattr(slave)[3] & termios.ISIG)

    def test_reads_a_single_keypress_without_a_newline(self):
        master, _, _, keys = self.terminal()
        os.write(master, b"a")
        self.assertEqual(keys.poll(), ["arm"])

    def test_restores_the_terminal_on_close(self):
        import termios
        _, slave, before, keys = self.terminal()
        keys.close()
        self.assertEqual(termios.tcgetattr(slave), before)

    def test_closing_twice_is_harmless(self):
        _, _, _, keys = self.terminal()
        keys.close()
        keys.close()


class NullInputTests(unittest.TestCase):
    def test_is_always_empty(self):
        keys = NullInput()
        self.assertEqual(keys.poll(), [])
        keys.close()


if __name__ == "__main__":
    unittest.main()
