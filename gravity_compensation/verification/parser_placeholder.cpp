// SPDX-License-Identifier: LGPL-2.1-or-later
// Test-only DT_NEEDED placeholder. It is NOT an implementation of kdl_parser.
// The ABI probe supplies a constructed KDL solver and never invokes URDF parsing.
extern "C" int arx_gravity_parser_placeholder() { return 0; }
