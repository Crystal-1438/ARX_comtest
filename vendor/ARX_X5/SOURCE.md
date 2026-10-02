# Vendor SDK provenance

- Upstream repository: https://gitee.com/li-bozha0/ARX_X5
- Pinned commit: `c78328785ea23a81d908e1dcc551eca992f2f1e9`
- Upstream license: [BSD 3-Clause](LICENSE), retained verbatim.
- Included subtree: `py/arx_x5_python/`, including original Python/C++ sources,
  URDFs, build scripts, headers, documentation, and x86_64 shared libraries.
- Excluded: tracked Python bytecode/cache directories and duplicated installed
  `bimanual/api/**/include/` headers. The source headers remain under `bimanual/lib/`.
- All copied files are unchanged. [SHA256SUMS](SHA256SUMS) records their checksums
  plus the upstream license; paths are relative to this directory. Verify with
  `sha256sum -c SHA256SUMS` from this directory.

The supplied Python extensions target CPython 3.12 on Linux x86_64. Native runtime
dependencies (including KDL / kdl_parser) are not bundled. The CMake file mentions
ARM64 support, but this upstream snapshot does not supply its ARM64 core library.
Use a matching vendor library and rebuild for other interpreter/CPU combinations.

The original SDK examples may issue motor commands. Start with this project's
mock backend and use `app.py --mode preflight` before attempting hardware use.
