# Release readiness — transcribe-translate

A short pre-release checklist for `0.1.0`.

## Confirmed

- [x] **Tests pass** with the standard library only (`python -m unittest discover -s tests -v`); no pytest, no network, no model downloads.
- [x] **Import-safe without heavy deps** — the package imports and `--dry-run` works with `faster-whisper` / `deep-translator` / `torch` *not* installed (verified by the test suite, which runs in exactly that environment). CI installs with `pip install -e . --no-deps`.
- [x] **No secrets** committed (API keys, tokens, credentials).
- [x] **No personal/absolute paths** baked into source or docs — examples use generic relative paths.
- [x] **src layout** (`src/transcribe_translate/`) with `pyproject.toml` `packages.find` pointed at `src`.
- [x] **Console entry point** `transcribe-translate = transcribe_translate.cli:main`.
- [x] **License** present (MIT, 2026, "The transcribe-translate authors").
- [x] **README** with badge, purpose, ffmpeg note, install, usage with real I/O example, dry-run example, roadmap, license.
- [x] **CI** workflow (`.github/workflows/tests.yml`) runs unittest on Python 3.9 / 3.11 / 3.12.
- [x] **Dependencies** declared (`faster-whisper`, `deep-translator`) with a `dev` extra (`build`).

## Known limitations

- Real transcription requires `ffmpeg` on `PATH` (system package, not installed by pip).
- Real transcription/translation are **not** exercised in CI — only the lazy-import seams and the injected-fake paths are tested. End-to-end behaviour with the actual models should be validated manually before relying on output quality.
- Translation uses Google Translate via `deep-translator`; it needs network access and is subject to that service's limits and changes.
- Whole-file processing only: very long audio is transcribed in one call, and the full transcript is sent to the translator in a single request.
- GPU selection is a simple heuristic (`nvidia-smi` on PATH unless `FORCE_CPU=1`); exotic setups may need manual environment tweaks.
