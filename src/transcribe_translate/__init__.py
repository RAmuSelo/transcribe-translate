"""transcribe-translate: transcribe an audio file and translate the text.

Heavy dependencies are imported lazily inside :mod:`transcribe_translate.core`,
so importing this package never pulls in ``faster-whisper`` or
``deep-translator``.
"""

from .core import (
    build_plan,
    ensure_ffmpeg,
    load_model,
    run,
    transcribe_auto,
    translate_text,
)

__version__ = "0.1.0"

__all__ = [
    "ensure_ffmpeg",
    "load_model",
    "transcribe_auto",
    "translate_text",
    "build_plan",
    "run",
    "__version__",
]
