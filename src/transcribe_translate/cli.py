"""Command-line interface for transcribe-translate."""

import argparse
import os
import sys

from . import __version__
from .core import build_plan, run


def build_parser():
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="transcribe-translate",
        description=(
            "Transcribe an audio file (auto language detection) and translate "
            "the text into a target language."
        ),
    )
    parser.add_argument("audio", help="Path to the audio file to process.")
    parser.add_argument(
        "--target-lang",
        default="fr",
        help="Target language code for translation (default: fr).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Whisper model size; sets the WHISPER_MODEL environment variable.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned output paths without transcribing (no heavy deps).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {0}".format(__version__),
    )
    return parser


def main(argv=None):
    """Entry point for the ``transcribe-translate`` console script."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.model:
        os.environ["WHISPER_MODEL"] = args.model

    if args.dry_run:
        plan = build_plan(args.audio, target_lang=args.target_lang)
        print("Plan (dry run):")
        print("  audio:           {0}".format(plan["audio"]))
        print("  audio exists:    {0}".format(plan["audio_exists"]))
        print("  target language: {0}".format(plan["target_lang"]))
        print("  transcription -> {0}".format(plan["out_transcription"]))
        print("  translation   -> {0}".format(plan["out_translation"]))
        return 0

    if not os.path.isfile(args.audio):
        parser.error("audio file not found: {0}".format(args.audio))

    result = run(args.audio, target_lang=args.target_lang)
    print("Detected language: {0}".format(result["lang"]))
    print("Transcription written to: {0}".format(result["out_transcription"]))
    print("Translation written to:   {0}".format(result["out_translation"]))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
