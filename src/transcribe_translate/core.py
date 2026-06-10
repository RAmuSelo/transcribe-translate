"""Core logic for transcribe-translate.

Transcribe a single audio file (with automatic language detection) and
translate the resulting text into a target language.

The heavy dependencies (``faster-whisper`` and ``deep-translator``) are
imported lazily, *inside* the functions that need them, and every entry point
accepts an injection seam (a model loader or a translator). This keeps the
module importable — and the ``--dry-run`` plan mode usable — even when those
packages are not installed.
"""

import os
import shutil
from pathlib import Path

__all__ = [
    "ensure_ffmpeg",
    "load_model",
    "transcribe_auto",
    "translate_text",
    "build_plan",
    "run",
]


def ensure_ffmpeg(which=shutil.which):
    """Raise ``RuntimeError`` unless an ``ffmpeg`` binary is on PATH.

    Args:
        which: Lookup callable, injectable for tests. Defaults to
            :func:`shutil.which`.

    Raises:
        RuntimeError: If ``ffmpeg`` is not found.
    """
    if which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found in PATH")


def load_model():
    """Lazily import faster-whisper and build a ``WhisperModel``.

    Reads two environment variables:

    - ``WHISPER_MODEL`` — model size (default ``"medium"``).
    - ``FORCE_CPU`` — when ``"1"``, forces CPU even if a GPU is present.

    GPU is selected when ``FORCE_CPU`` is not ``"1"`` and ``nvidia-smi`` is on
    PATH. The ``faster_whisper`` import happens here so the module stays
    importable without it.

    Returns:
        A ``faster_whisper.WhisperModel`` instance.
    """
    from faster_whisper import WhisperModel

    model_size = os.getenv("WHISPER_MODEL", "medium")
    use_gpu = os.getenv("FORCE_CPU", "0") != "1" and shutil.which("nvidia-smi")
    device = "cuda" if use_gpu else "cpu"
    compute_type = "float16" if device == "cuda" else "int8_float16"
    return WhisperModel(model_size, device=device, compute_type=compute_type)


def transcribe_auto(audio_path, model_loader=load_model):
    """Transcribe ``audio_path`` with automatic language detection.

    Args:
        audio_path: Path to the audio file.
        model_loader: Callable returning a model object exposing
            ``transcribe(path, ...) -> (segments, info)``. Injectable for
            tests; defaults to :func:`load_model`.

    Returns:
        tuple: ``(text, language, language_probability)`` where ``text`` is the
        concatenated, stripped transcript.
    """
    model = model_loader()
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True,
        language=None,
        task="transcribe",
    )
    text = "".join(segment.text for segment in segments).strip()
    language = getattr(info, "language", None)
    probability = getattr(info, "language_probability", 0.0)
    return text, language, probability


def translate_text(text, target="fr", translator=None):
    """Translate ``text`` into ``target``.

    Args:
        text: Source text.
        target: Target language code (default ``"fr"``).
        translator: Optional injected translator. May be either a callable
            ``translator(text) -> str`` or an object with a
            ``.translate(text) -> str`` method. When ``None``, a
            ``deep_translator.GoogleTranslator`` is built lazily.

    Returns:
        str: The translated text.
    """
    if translator is None:
        from deep_translator import GoogleTranslator

        return GoogleTranslator(source="auto", target=target).translate(text)
    if hasattr(translator, "translate"):
        return translator.translate(text)
    return translator(text)


def build_plan(audio_path, target_lang="fr"):
    """Describe the planned outputs without importing any heavy dependency.

    Args:
        audio_path: Path to the audio file.
        target_lang: Target language code (default ``"fr"``).

    Returns:
        dict: ``{"audio": str, "audio_exists": bool, "target_lang": str,
        "out_transcription": str, "out_translation": str}``.
    """
    path = Path(audio_path)
    stem = path.stem
    parent = path.parent
    out_transcription = str(parent / "{0}_transcription.txt".format(stem))
    out_translation = str(parent / "{0}_{1}.txt".format(stem, target_lang))
    return {
        "audio": str(path),
        "audio_exists": path.is_file(),
        "target_lang": target_lang,
        "out_transcription": out_transcription,
        "out_translation": out_translation,
    }


def run(
    audio_path,
    target_lang="fr",
    dry_run=False,
    model_loader=load_model,
    translator=None,
    write=True,
):
    """Transcribe and translate ``audio_path``, optionally writing files.

    In ``dry_run`` mode the function returns :func:`build_plan` immediately and
    imports nothing heavy. Otherwise it transcribes, translates, and (when
    ``write`` is True) writes ``<stem>_transcription.txt`` and
    ``<stem>_<lang>.txt`` next to the audio file.

    Args:
        audio_path: Path to the audio file.
        target_lang: Target language code (default ``"fr"``).
        dry_run: When True, return the plan without doing any work.
        model_loader: Injectable model loader (see :func:`transcribe_auto`).
        translator: Injectable translator (see :func:`translate_text`).
        write: When True, write the output files to disk.

    Returns:
        dict: In dry-run mode, the plan from :func:`build_plan` plus
        ``"dry_run": True``. Otherwise ``{"text", "translation", "lang",
        "out_transcription", "out_translation", "dry_run"}``.
    """
    plan = build_plan(audio_path, target_lang=target_lang)
    if dry_run:
        result = dict(plan)
        result["dry_run"] = True
        return result

    text, lang, _prob = transcribe_auto(audio_path, model_loader=model_loader)
    translation = translate_text(text, target=target_lang, translator=translator)

    if write:
        with open(plan["out_transcription"], "w", encoding="utf-8") as handle:
            handle.write(text)
        with open(plan["out_translation"], "w", encoding="utf-8") as handle:
            handle.write(translation)

    return {
        "text": text,
        "translation": translation,
        "lang": lang,
        "out_transcription": plan["out_transcription"],
        "out_translation": plan["out_translation"],
        "dry_run": False,
    }
