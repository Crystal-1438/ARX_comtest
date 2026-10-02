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


class AnchorTests(unittest.TestCase):
    """Choosing the turn from the arm's pose, at the moment the arm is enabled.

    The map's ``reference_deg`` no longer takes part: what a session started
    reading says nothing about which turn it is on, and the arm does.
    """

    def decoder(self, reference=None):
        return LeaderUartDecoder(LeaderMap(joints=(JointMap(),) * 6, calibrated=True,
                                           reference_deg=reference))

    @staticmethod
    def arm_at(*degrees):
        """The measured joint vector whose pose corresponds to these leader angles."""
        return tuple(math.radians(value) for value in degrees)

    def test_the_arm_decides_the_turn_not_the_reference_pose(self):
        # The core of the change: this session's first frame is nowhere near the
        # calibrated pose -- 90 degrees out on J3, which the old rule refused --
        # yet the arm is in exactly that pose, so there is nothing to refuse.
        decoder = self.decoder(reference=[79.5, 328.1, 16.0, 235.3, 287.5, 208.5])
        feed(decoder, VALID)
        self.assertIsNone(decoder.anchor(self.arm_at(*VALID_DEG)))
        self.assertTrue(decoder.last_telemetry["anchor"]["ok"])

    def test_a_pose_the_arm_is_in_arms_with_no_bias(self):
        decoder = self.decoder()
        feed(decoder, VALID)
        self.assertIsNone(decoder.anchor(self.arm_at(*VALID_DEG)))
        self.assertEqual(decoder.mapper.bias, [0.0] * 6)

    def test_the_bias_carries_the_stream_past_the_rollover(self):
        # J1 reads 4.0 where the arm's pose calls for 354.0: ten degrees apart, but on
        # opposite sides of the encoder's 0/360 seam. The whole turn of bias is
        # what makes the rest of the stream continue from there instead of
        # jumping back to 4.
        decoder = self.decoder()
        feed(decoder, b"40,3281,1060,2353,2875,2085,500")
        self.assertIsNone(decoder.anchor(self.arm_at(354.0, *VALID_DEG[1:])))
        self.assertEqual(decoder.mapper.bias[0], 360.0)
        # 5.0 after 4.0 is the next sample, and 365 is where it belongs.
        self.assertAlmostEqual(feed(decoder, b"50,3281,1060,2353,2875,2085,500")[0].joints[0],
                               math.radians(365.0))

    def test_a_pose_the_arm_is_not_in_is_refused(self):
        decoder = self.decoder()
        feed(decoder, VALID)
        blocker = decoder.anchor(self.arm_at(169.5, *VALID_DEG[1:]))
        self.assertIn("J1", blocker)
        self.assertFalse(decoder.last_telemetry["anchor"]["ok"])
        self.assertEqual(decoder.mapper.bias, [0.0] * 6)

    def test_the_refusal_says_how_far_to_turn_as_well_as_how_far_off(self):
        # Two numbers again, and now the same size: the turn is the physical
        # move the hand makes and the command is what the arm would be told.
        # They differ only in sign, so leading with either one alone reads as
        # the wrong size to half the people reading it.
        decoder = self.decoder()
        feed(decoder, b"40,3281,1060,2353,2875,2085,500")
        blocker = decoder.anchor(self.arm_at(44.0, *VALID_DEG[1:]))
        self.assertIn("reads 4.0", blocker)      # where the leader is
        self.assertIn("arm's pose calls for 44.0", blocker)
        self.assertIn("turn it +40.0", blocker)  # what the operator has to do
        self.assertIn("move J1 -40.0 deg", blocker)  # and what arming would do instead

    def test_it_is_the_same_number_the_refusal_quotes(self):
        # The point of watching these: the line reaches zero exactly when
        # pressing a would work, because it is the same measurement.
        decoder = self.decoder()
        feed(decoder, b"40,3281,1060,2353,2875,2085,500")
        arm = self.arm_at(44.0, *VALID_DEG[1:])
        reading = decoder.distance(arm)
        self.assertAlmostEqual(reading["turn_deg"][0], 40.0)
        self.assertEqual(reading["outside"], [0])
        self.assertEqual(reading["tolerance_deg"], 30.0)
        self.assertIn("turn it +40.0", decoder.anchor(arm))

    def test_watching_never_chooses_the_turn(self):
        # This pose anchors. Watching it must still leave the bias alone: a bias
        # picked up while the leader merely passes through would be carried into
        # the session, and the turn is only decided at the moment of arming.
        decoder = self.decoder()
        feed(decoder, VALID)
        decoder.distance(self.arm_at(*VALID_DEG))
        self.assertEqual(decoder.mapper.bias, [0.0] * 6)

    def test_it_reaches_zero_in_the_arm_s_pose(self):
        decoder = self.decoder()
        feed(decoder, VALID)
        reading = decoder.distance(self.arm_at(*VALID_DEG))
        # Radians and back does not round-trip exactly on every joint, so the
        # residue is 1e-14 and not 0 -- which is why the readout is printed to
        # one decimal and the tolerance is a whole number of degrees.
        for index, turn in enumerate(reading["turn_deg"]):
            with self.subTest(joint=index + 1):
                self.assertAlmostEqual(turn, 0.0, places=9)
        self.assertEqual(reading["outside"], [])

    def test_before_a_frame_there_is_nothing_to_report(self):
        self.assertIsNone(self.decoder().distance((0.0,) * 6))

    def test_the_refusal_quotes_the_reading_the_board_shows(self):
        # The operator's live refusal: the leader had been turned past the
        # rollover, so the mapper's continuous value was -72.1 while the board
        # read 287.9. Both are the same angle, but only one of them is on the
        # screen being looked at, and the turn is measured from it.
        decoder = self.decoder()
        feed(decoder, b"40,3281,1060,2353,2875,2085,500")
        feed(decoder, b"2879,3281,1060,2353,2875,2085,500")   # J1 down through zero
        self.assertAlmostEqual(decoder.mapper.continuous[0], -72.1)
        blocker = decoder.anchor(self.arm_at(323.0, *VALID_DEG[1:]))
        self.assertIn("reads 287.9 deg", blocker)
        self.assertIn("arm's pose calls for 323.0", blocker)
        self.assertIn("turn it +35.1 deg", blocker)
        self.assertNotIn("-72.1", blocker)

    def test_the_refusal_names_every_joint_that_is_out(self):
        # Naming only the worst sends the operator round once per joint.
        decoder = self.decoder()
        feed(decoder, VALID)
        arm = list(VALID_DEG)
        arm[0] = 169.5   # 90 deg out
        arm[2] = 6.0     # 100 deg out, so this is the worst
        blocker = decoder.anchor(self.arm_at(*arm))
        self.assertIn("J1", blocker)
        self.assertIn("J3", blocker)
        self.assertEqual(decoder.last_telemetry["anchor"]["worst_joint"], 2)

    def test_arming_before_any_frame_arrives_is_refused_without_raising(self):
        # Refused, not crashed: this is called from the controller's arm
        # transition, so an exception here would come out of the program.
        decoder = self.decoder()
        blocker = decoder.anchor(self.arm_at(*VALID_DEG))
        self.assertIn("no leader frame", blocker)
        self.assertIsNone(decoder.last_telemetry)
        self.assertEqual(decoder.mapper.bias, [0.0] * 6)

    def test_a_session_that_was_never_anchored_reports_null(self):
        decoder = self.decoder()
        feed(decoder, VALID)
        self.assertIsNone(decoder.last_telemetry["anchor"])

    def test_a_warmup_frame_is_not_an_origin_to_anchor_against(self):
        decoder = self.decoder()
        self.assertEqual(feed(decoder, b"-1,-1,-1,-1,-1,-1,500"), [])
        self.assertIn("no leader frame", decoder.anchor(self.arm_at(*VALID_DEG)))

    def test_a_board_reset_drops_the_bias_and_needs_another_anchor(self):
        # The encoders start over, so the origin the bias was chosen against is
        # gone; carrying it over would apply a whole turn nobody asked for.
        decoder = self.decoder()
        feed(decoder, b"40,3281,1060,2353,2875,2085,500")
        self.assertIsNone(decoder.anchor(self.arm_at(354.0, *VALID_DEG[1:])))
        self.assertEqual(feed(decoder, HANDSHAKE), [])
        self.assertEqual(decoder.mapper.bias, [0.0] * 6)
        self.assertIsNone(decoder.last_telemetry["anchor"])

    def test_a_local_reset_drops_the_bias_too(self):
        decoder = self.decoder()
        feed(decoder, b"40,3281,1060,2353,2875,2085,500")
        decoder.anchor(self.arm_at(354.0, *VALID_DEG[1:]))
        decoder.reset()
        self.assertEqual(decoder.mapper.bias, [0.0] * 6)
        self.assertIn("no leader frame", decoder.anchor(self.arm_at(*VALID_DEG)))

    def test_a_failing_batch_drops_the_bias(self):
        decoder = self.decoder()
        feed(decoder, VALID)
        decoder.anchor(self.arm_at(*VALID_DEG))
        with self.assertRaises(ProtocolError):
            feed(decoder, b"795,3281,1060,2353,2875,2085,1001")
        self.assertEqual(decoder.mapper.bias, [0.0] * 6)

    def test_the_anchor_survives_a_blank_read(self):
        # The report rate is below the stream rate, so most printed frames land
        # on a loop that consumed nothing. The verdict has to still be there.
        decoder = self.decoder()
        feed(decoder, VALID)
        decoder.anchor(self.arm_at(*VALID_DEG))
        decoder.feed(b"")
        self.assertTrue(decoder.last_telemetry["anchor"]["ok"])


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
