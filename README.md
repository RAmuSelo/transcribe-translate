# transcribe-translate

[![Tests](https://github.com/RAmuSelo/transcribe-translate/actions/workflows/tests.yml/badge.svg)](https://github.com/RAmuSelo/transcribe-translate/actions/workflows/tests.yml)

`transcribe-translate` takes one audio file, transcribes it with automatic language detection (via [faster-whisper](https://github.com/SYSTRAN/faster-whisper)), then translates the transcript into a target language (French by default, via [deep-translator](https://github.com/nidhaloff/deep-translator)). It writes two files next to the audio: `<stem>_transcription.txt` and `<stem>_<lang>.txt`.

The heavy machine-learning dependencies are imported **lazily**, so the package itself imports instantly and the `--dry-run` plan mode runs even on a machine where `faster-whisper`, `deep-translator`, and `torch` are not installed.

> **System requirement:** real transcription needs [`ffmpeg`](https://ffmpeg.org/) on your `PATH`. It is a system package, not a Python one — install it via your OS package manager (e.g. `apt install ffmpeg`, `brew install ffmpeg`).

## Why this exists

A common need is dead simple to describe and annoyingly fiddly to wire up: "here's a voice memo in some language — give me the text and an English (or French) version." Doing it by hand means picking a Whisper model, remembering the right `device`/`compute_type` flags, gluing a translator on the end, and naming the output files consistently. This tool packages that one job behind a single command and, crucially, keeps the import graph clean so you can script a `--dry-run` to check what *would* happen without paying the cost of loading a multi-gigabyte model.

## Install

```
python -m pip install transcribe-translate
```

Or from a checkout:

```
python -m pip install -e .
```

This pulls in `faster-whisper` and `deep-translator`. Remember to install `ffmpeg` separately.

## Usage

Transcribe and translate a French voice note into English:

```
transcribe-translate memo.ogg --target-lang en
```

Example output:

```
Detected language: fr
Transcription written to: memo_transcription.txt
Translation written to:   memo_en.txt
```

Pick a different Whisper model size (sets the `WHISPER_MODEL` environment variable):

```
transcribe-translate memo.ogg --model small
```

### Dry run (no heavy dependencies needed)

See exactly which files would be produced, without loading a model or hitting the network:

```
transcribe-translate memo.ogg --dry-run
```

```
Plan (dry run):
  audio:           memo.ogg
  audio exists:    True
  target language: fr
  transcription -> memo_transcription.txt
  translation   -> memo_fr.txt
```

If the audio file is missing (and you are not in `--dry-run`), the command prints a clear error and exits with status `2`.

### Environment variables

| Variable | Effect |
| --- | --- |
| `WHISPER_MODEL` | Model size to load (default `medium`). Also set by `--model`. |
| `FORCE_CPU` | Set to `1` to force CPU even when a GPU is detected. |

## Use as a library

The core functions accept injection seams, so you can drive them with your own model or translator (handy for tests and custom pipelines):

```python
from transcribe_translate import run

result = run(
    "memo.ogg",
    target_lang="en",
    model_loader=lambda: my_model,      # object with .transcribe(...)
    translator=lambda text: my_translate(text),
)
print(result["text"], result["translation"])
```

`build_plan(audio_path, target_lang)` returns the planned output paths without importing anything heavy.

## Roadmap

- Batch mode for a folder of audio files.
- Optional SRT/VTT subtitle output with timestamps.
- Pluggable translation backends beyond Google Translate.
- A flag to keep the detected-language transcript only (skip translation).

These are intentions, not commitments; issues and pull requests are welcome.

## License

MIT — see [LICENSE](LICENSE).
