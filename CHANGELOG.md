# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- CONTRIBUTING.md
- CHANGELOG.md

### Planned

- Batch mode for a folder of audio files.
- Optional SRT/VTT subtitle output with timestamps.
- Pluggable translation backends beyond Google Translate.
- A flag to keep the detected-language transcript only (skip translation).

## [0.1.0] - 2026-06-10

### Added

- Transcribe one audio file with automatic language detection (via faster-whisper) and translate the transcript into a target language (French by default, via deep-translator).
- Write two files next to the audio: `<stem>_transcription.txt` and `<stem>_<lang>.txt`.
- Lazy imports of the heavy machine-learning dependencies, so the package imports instantly and `--dry-run` runs even without `faster-whisper`, `deep-translator`, or `torch` installed.
- `--dry-run` plan mode that prints the planned output paths without loading a model or hitting the network.
- `--target-lang` to choose the translation language.
- `--model` to pick the Whisper model size (also via the `WHISPER_MODEL` environment variable).
- `FORCE_CPU` environment variable to force CPU even when a GPU is detected.
- Clear error and exit status `2` when the audio file is missing (outside `--dry-run`).
- Library API with injection seams (`run(...)`, `build_plan(...)`) for custom models, translators, and tests.
- Stdlib unittest test suite.
- GitHub Actions CI (Python 3.9/3.11/3.12).
- MIT license.

[Unreleased]: https://github.com/RAmuSelo/transcribe-translate/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/RAmuSelo/transcribe-translate/releases/tag/v0.1.0
