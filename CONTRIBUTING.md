# Contributing to transcribe-translate

Thanks for your interest in improving `transcribe-translate`. Bug reports,
documentation fixes, and well-scoped features are all welcome. This tool does
one job — transcribe an audio file and translate the text — and contributions
that keep it focused are the easiest to merge.

## Ground rules

- **The tool installs nothing at runtime.** It must never shell out to a package
  manager or auto-install models, Python packages, or system software. If a
  dependency is missing, the tool's job is to fail with a clear message, not to
  fix the environment.
- **Heavy dependencies are lazy-imported.** `faster-whisper`, `deep-translator`,
  and `torch` must only be imported inside the functions that actually need them,
  never at module import time. This is what lets the package import instantly and
  lets `--dry-run` work on a machine without the models installed. Do not move
  these imports to the top of a module.
- **ffmpeg is a system dependency the user installs.** It is not a Python package
  and the tool does not install it. Keep it documented as a user-installed
  requirement.
- Be respectful and constructive in issues and pull requests.

## Development setup

Install in editable mode **without** the heavy dependencies, then run the tests:

```
pip install -e . --no-deps
python -m unittest discover -s tests
```

The `--no-deps` flag is deliberate: the test suite **mocks** the model and
translator, so it needs **no network, no model download, and no ffmpeg**. You do
not need `faster-whisper`, `deep-translator`, or `torch` installed to run the
tests. (Install the full dependencies only when you want to exercise real
transcription manually.)

## Making a change

- Keep pull requests small and focused on a single change.
- Add `unittest` tests for any new behavior or bug fix. Use the existing
  injection seams (custom `model_loader` / `translator`) so tests stay offline
  and never download a model or call a network service.
- Keep CI green on Python 3.9, 3.11, and 3.12.
- Do not add new runtime dependencies without discussion in an issue first.
- Preserve the lazy-import boundary — a change that makes a heavy library import
  at module load time will break `--dry-run` and the test setup.
- Update the README and `CHANGELOG.md` (`Unreleased` section) when behavior or
  usage changes.

## Reporting bugs

Open an issue with the command you ran, what you expected, and what happened.
Include your OS, Python version, and whether `ffmpeg` is on your `PATH`.

**Never paste secrets, access tokens, or absolute paths from your machine.**
Redact local paths and anything sensitive before sharing logs or examples.

## Scope

`transcribe-translate` transcribes a single audio file (with automatic language
detection) and translates the resulting text into one target language, writing a
transcription file and a translation file next to the audio.

It is intentionally **not**:

- a batch processor today (a folder/batch mode is on the roadmap, but the current
  tool handles one file per invocation);
- a subtitle/timestamp tool (SRT/VTT output is on the roadmap, not a current
  feature);
- an installer or environment manager — it will tell you what is missing
  (`ffmpeg`, a model package) but will never install it for you;
- a diarization or speaker-separation tool.

Changes that pull in always-on heavy dependencies, auto-install software, or
broaden the tool well beyond "transcribe one file, translate it" are likely out
of scope. When in doubt, open an issue first.
