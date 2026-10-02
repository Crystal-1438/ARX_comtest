import math
import unittest

from leader_decoder import HANDSHAKE, LeaderUartDecoder, parse_line
from leader_map import JointMap, LeaderMap
from protocol import Command, ProtocolError


def calibrated(**overrides):
    return LeaderMap(joints=(JointMap(**overrides),) * 6, calibrated=True)


def feed(decoder, *lines):
    return decoder.feed(b"".join(line + b"\r\n" for line in lines))


VALID = b"795,3281,1060,2353,2875,2085,500"
# VALID in degrees, which is what a reference pose is recorded in.
VALID_DEG = [79.5, 328.1, 106.0, 235.3, 287.5, 208.5]


class ParseTests(unittest.TestCase):
    def test_parses_a_captured_packet(self):
        self.assertEqual(parse_line(VALID), (795, 3281, 1060, 2353, 2875, 2085, 500))

    def test_drops_everything_that_is_not_exactly_seven_fields(self):
        for line in (b"0123456789", b"", b"1,2,3,4,5,6", b"1,2,3,4,5,6,7,8",
                     b"795,3281,1060,2353,2875,2085,", b"795,3281,1060,2353,2875,2085,500,0"):
            with self.subTest(line=line):
                self.assertIsNone(parse_line(line))

    def test_rejects_shapes_that_int_would_quietly_accept(self):
        for line in (b" 795,3281,1060,2353,2875,2085,500",
                     b"795,3281,1060,2353,2875,2085, 500",
                     b"+795,3281,1060,2353,2875,2085,500",
                     b"795,3281,1060,2353,2875,2085,5.0",
                     b"795,3281,1060,2353,2875,2085,5e2",
                     b"795,3281,1060,2353,2875,2085,x00"):
            with self.subTest(line=line):
                self.assertIsNone(parse_line(line))

    def test_accepts_the_documented_no_data_sentinel(self):
        self.assertEqual(parse_line(b"-1,3281,1060,2353,2875,2085,500")[0], -1)


class DecoderTests(unittest.TestCase):
    def decoder(self, mapping=None):
        return LeaderUartDecoder(mapping or calibrated())

    def test_emits_one_target_in_vendor_frame(self):
        decoder = self.decoder()
        commands = feed(decoder, VALID)
        self.assertEqual(len(commands), 1)
        command = commands[0]
        self.assertIsInstance(command, Command)
        self.assertEqual((command.kind, command.deadman), ("target", True))
        self.assertEqual(len(command.joints), 6)
        self.assertAlmostEqual(command.joints[0], math.radians(79.5))
        self.assertAlmostEqual(command.joints[5], math.radians(208.5))

    def test_returns_only_the_newest_frame_of_a_batch(self):
        decoder = self.decoder()
        commands = feed(decoder, VALID, b"0,0,0,0,0,0,0")
        self.assertEqual(len(commands), 1)
        self.assertAlmostEqual(commands[0].joints[0], 0.0)

    def test_sequence_numbers_strictly_increase(self):
        decoder = self.decoder()
        self.assertEqual(feed(decoder, VALID)[0].seq, 1)
        self.assertEqual(feed(decoder, VALID)[0].seq, 2)
        # Frames consumed without producing a command must not burn a sequence.
        self.assertEqual(feed(decoder, HANDSHAKE), [])
        self.assertEqual(feed(decoder, VALID)[0].seq, 3)

    def test_a_half_written_line_would_corrupt_the_next_one(self):
        decoder = self.decoder()
        decoder.feed(VALID[:20])
        self.assertEqual(decoder.feed(b"0,0,0,0,0,0,0\r\n"), [])
        self.assertEqual(decoder.dropped, 1)

    def test_reset_discards_that_half_written_line(self):
        decoder = self.decoder()
        decoder.feed(VALID[:20])
        decoder.reset()
        self.assertEqual(len(decoder.feed(b"0,0,0,0,0,0,0\r\n")), 1)
        self.assertEqual(decoder.dropped, 0)

    def test_failing_batch_still_publishes_counters_and_a_reason(self):
        decoder = self.decoder()
        feed(decoder, VALID)
        with self.assertRaises(ProtocolError):
            feed(decoder, HANDSHAKE, b"795,3281,1060,2353,2875,2085,1001")
        self.assertEqual(decoder.last_telemetry["resets"], 1)
        self.assertIn("1001", decoder.last_telemetry["error"])

    def test_reassembles_a_frame_split_across_reads(self):
        decoder = self.decoder()
        self.assertEqual(decoder.feed(VALID[:20]), [])
        commands = decoder.feed(VALID[20:] + b"\r\n")
        self.assertAlmostEqual(commands[0].joints[0], math.radians(79.5))

    def test_a_stalled_stream_emits_nothing_rather_than_repeating_a_target(self):
        decoder = self.decoder()
        feed(decoder, VALID)
        # The controller's watchdog must be free to fire on an idle line.
        self.assertEqual(decoder.feed(b""), [])

    def test_the_last_frame_survives_a_batch_with_no_new_data(self):
        # Print rate is below stream rate, so reports routinely land on a loop
        # that consumed nothing; a blank frame there would look like a dead link.
        decoder = self.decoder()
        feed(decoder, VALID)
        stamped = decoder.last_telemetry["frame"]["host_monotonic"]
        decoder.feed(b"")
        frame = decoder.last_telemetry["frame"]
        self.assertEqual(frame["fields"][0], 795)
        # Stale, not re-dated: an unchanged stamp is how the operator sees that.
        self.assertEqual(frame["host_monotonic"], stamped)

    def test_counts_every_frame_not_just_the_ones_it_hands_over(self):
        # The wire carries no sequence number, so a received-packet count is the
        # only way to notice that the board is dropping frames.
        decoder = self.decoder()
        feed(decoder, VALID, b"0,0,0,0,0,0,0", b"1,1,1,1,1,1,1")
        self.assertEqual(decoder.frames, 3)
        self.assertEqual(decoder.seq, 1)  # only the newest one was emitted

    def test_a_fresh_frame_moves_the_stamp(self):
        decoder = self.decoder()
        feed(decoder, VALID)
        stamped = decoder.last_telemetry["frame"]["host_monotonic"]
        feed(decoder, b"0,0,0,0,0,0,0")
        self.assertGreaterEqual(decoder.last_telemetry["frame"]["host_monotonic"], stamped)
        self.assertEqual(decoder.last_telemetry["frame"]["fields"][0], 0)

    def test_handshake_is_recognised_rather_than_counted_as_corruption(self):
        decoder = self.decoder()
        self.assertEqual(feed(decoder, HANDSHAKE), [])
        self.assertEqual((decoder.dropped, decoder.resets), (0, 1))

    def test_no_data_sentinel_is_not_zero_degrees(self):
        decoder = self.decoder()
        self.assertEqual(feed(decoder, b"-1,3281,1060,2353,2875,2085,500"), [])
        self.assertEqual(decoder.no_data, 1)
        self.assertIsNone(decoder.last_telemetry["frame"])

    def test_declares_that_the_wire_carries_no_arm_or_stop(self):
        self.assertIs(LeaderUartDecoder.provides_arm, False)

    def test_reports_the_map_it_actually_loaded(self):
        decoder = self.decoder()
        self.assertTrue(decoder.calibrated)
        feed(decoder, VALID)
        self.assertTrue(decoder.last_telemetry["calibrated"])
        self.assertEqual(decoder.last_telemetry["frame"]["gripper"], 500)
        self.assertAlmostEqual(decoder.last_telemetry["frame"]["angle_deg"][1], 328.1)


class StartupTransientTests(unittest.TestCase):
    """docs/uart_packet.md section 4: the first packets after a board reset may
    still read -1 while the encoder waits for its first PWM period."""

    def decoder(self):
        return LeaderUartDecoder(calibrated())

    def test_no_data_frames_are_dropped_while_the_stream_warms_up(self):
        decoder = self.decoder()
        self.assertEqual(feed(decoder, b"-1,-1,-1,-1,-1,-1,500"), [])
        self.assertEqual(decoder.no_data, 1)

    def test_no_data_after_a_valid_frame_is_a_fault(self):
        decoder = self.decoder()
        feed(decoder, VALID)
        with self.assertRaises(ProtocolError):
            feed(decoder, b"-1,3281,1060,2353,2875,2085,500")

    def test_a_warmup_drop_does_not_disable_the_later_fault(self):
        decoder = self.decoder()
        feed(decoder, b"-1,-1,-1,-1,-1,-1,500")
        feed(decoder, VALID)
        with self.assertRaises(ProtocolError):
            feed(decoder, VALID.replace(b"1060", b"-1"))

    def test_a_replugged_board_warms_up_again_behind_its_handshake(self):
        decoder = self.decoder()
        feed(decoder, VALID)
        self.assertEqual(feed(decoder, HANDSHAKE), [])
        self.assertEqual(feed(decoder, b"-1,3281,1060,2353,2875,2085,500"), [])

    def test_reset_alone_does_not_silence_a_real_fault(self):
        # reset() clears buffer state after an upstream error; it must not be
        # able to reclassify a dead encoder as a startup transient.
        decoder = self.decoder()
        feed(decoder, VALID)
        decoder.reset()
        with self.assertRaises(ProtocolError):
            feed(decoder, b"-1,3281,1060,2353,2875,2085,500")


class ReferenceTests(unittest.TestCase):
    """The unwrap origin is the first frame, so a session that starts away from
    the calibrated pose is off by that much before it moves at all."""

    def decoder(self, reference=VALID_DEG):
        return LeaderUartDecoder(LeaderMap(joints=(JointMap(),) * 6, calibrated=True,
                                           reference_deg=reference))

    def test_a_session_that_starts_at_the_reference_can_be_armed(self):
        decoder = self.decoder()
        feed(decoder, VALID)
        self.assertIsNone(decoder.startup_blocker)
        self.assertTrue(decoder.last_telemetry["reference"]["ok"])

    def test_a_session_that_starts_elsewhere_cannot_be_armed(self):
        decoder = self.decoder(reference=[79.5, 328.1, 16.0, 235.3, 287.5, 208.5])
        feed(decoder, VALID)
        blocker = decoder.startup_blocker
        self.assertIn("J3", blocker)
        self.assertIn("+90.0", blocker)
        self.assertEqual(decoder.last_telemetry["reference"]["worst_joint"], 2)

    def test_arming_before_any_frame_arrives_is_refused(self):
        # Otherwise the first key press is a race the gate always loses.
        self.assertIn("no leader frame", self.decoder().startup_blocker)

    def test_the_verdict_is_latched_to_the_first_frame(self):
        # The origin is already fixed by then; moving the leader back afterwards
        # cannot make the session correct.
        decoder = self.decoder(reference=[79.5, 328.1, 16.0, 235.3, 287.5, 208.5])
        feed(decoder, VALID)
        self.assertIsNotNone(decoder.startup_blocker)
        feed(decoder, VALID)
        self.assertIsNotNone(decoder.startup_blocker)

    def test_a_warmup_frame_does_not_become_the_origin(self):
        # The -1 frames are dropped before the mapper sees them, so the origin
        # has to be the first real frame and the check has to wait for it.
        decoder = self.decoder()
        self.assertEqual(feed(decoder, b"-1,-1,-1,-1,-1,-1,500"), [])
        self.assertIsNone(decoder.reference)
        feed(decoder, VALID)
        self.assertTrue(decoder.last_telemetry["reference"]["ok"])

    def test_a_new_origin_is_judged_again(self):
        # A board reset restarts the encoders, so the origin -- and therefore
        # the thing being judged -- is new.
        decoder = self.decoder(reference=[79.5, 328.1, 16.0, 235.3, 287.5, 208.5])
        feed(decoder, VALID)
        self.assertIsNotNone(decoder.startup_blocker)
        self.assertEqual(feed(decoder, HANDSHAKE), [])
        feed(decoder, b"796,3281,1060,2353,2875,2085,500")
        # 79.6 against a reference of 79.5: only J3 was ever wrong.
        self.assertIsNotNone(decoder.startup_blocker)
        self.assertIn("J3", decoder.startup_blocker)

    def test_a_reset_rejudges_against_whatever_comes_next(self):
        decoder = self.decoder()
        feed(decoder, VALID)
        decoder.reset()
        feed(decoder, b"30,3281,1060,2353,2875,2085,500")
        self.assertIn("J1", decoder.startup_blocker)

    def test_a_map_without_a_reference_is_reported_not_gated(self):
        # Maps written before the field existed keep working, exactly as well
        # as they did before it: the readout has to say they went unchecked.
        decoder = LeaderUartDecoder(calibrated())
        feed(decoder, VALID)
        self.assertIsNone(decoder.startup_blocker)
        reference = decoder.last_telemetry["reference"]
        self.assertFalse(reference["checked"])
        self.assertIn("reference_deg", reference["why"])


class RangeTests(unittest.TestCase):
    """No checksum: an out-of-range field is the only corruption we can see."""

    def decoder(self):
        return LeaderUartDecoder(calibrated())

    def reject(self, line):
        with self.assertRaises(ProtocolError):
            feed(self.decoder(), line)

    def test_rejects_out_of_range_fields(self):
        for line in (b"3600,3281,1060,2353,2875,2085,500",
                     b"-2,3281,1060,2353,2875,2085,500",
                     b"795,3281,1060,2353,2875,2085,1001",
                     b"795,3281,1060,2353,2875,2085,-1"):
            with self.subTest(line=line):
                self.reject(line)

    def test_a_bad_frame_cannot_hide_behind_a_good_one_in_the_same_batch(self):
        decoder = self.decoder()
        with self.assertRaises(ProtocolError):
            feed(decoder, VALID, b"795,3281,1060,2353,2875,2085,1001")
        # Nothing was returned, and the buffer is not left half-consumed.
        self.assertEqual(feed(decoder, VALID)[0].seq, 1)

    def test_rejects_an_overlong_frame(self):
        self.reject(b"0" * 1100)

    def test_rejects_an_unterminated_overlong_frame(self):
        with self.assertRaises(ProtocolError):
            self.decoder().feed(b"0" * 1100)


if __name__ == "__main__":
    unittest.main()
