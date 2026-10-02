# Agent working notes

- Read `HANDOFF.md` first for confirmed requirements, verification status and next steps.
- This is the standalone delivery repository. Remote: `https://github.com/Crystal-1438/ARX_comtest.git`.
- Use mock/PTY tests for software verification. Importing SDK classes for introspection is different
  from constructing `InterfacesPy`, which starts vendor hardware threads and may enable motors.
- SOFT is zero torque, not true motor disable; preserve this distinction in code and documentation.
- Keep the pinned `vendor/ARX_X5` snapshot unchanged. Build outputs go to ignored `build/` and `.sdk/`.
- Serial wire format is not finalized. Extend the decoder interface rather than guessing hardware frames.
- Run `.venv/bin/python -m unittest discover -s tests -v` and relevant script/build checks for changes.
- User preference: review task-only diffs, commit small coherent changes after their checks, and push
  promptly to the configured remote. Do not force-push; preserve unrelated work and exclude credentials.
- Update `HANDOFF.md` when interface contracts, validation status or remaining work change.
