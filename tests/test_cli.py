"""Unit tests for transcribe_translate.cli.

No real dependencies, no network. The dry-run path must work with nothing
heavy installed.
"""

import io
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from transcribe_translate import cli


class ParserTests(unittest.TestCase):
    def test_defaults(self):
        parser = cli.build_parser()
        args = parser.parse_args(["clip.wav"])
        self.assertEqual(args.audio, "clip.wav")
        self.assertEqual(args.target_lang, "fr")
        self.assertIsNone(args.model)
        self.assertFalse(args.dry_run)

    def test_all_flags(self):
        parser = cli.build_parser()
        args = parser.parse_args(
            ["clip.wav", "--target-lang", "en", "--model", "small", "--dry-run"]
        )
        self.assertEqual(args.target_lang, "en")
        self.assertEqual(args.model, "small")
        self.assertTrue(args.dry_run)

    def test_version_exits_zero(self):
        with self.assertRaises(SystemExit) as ctx:
            with redirect_stdout(io.StringIO()):
                cli.main(["--version"])
        self.assertEqual(ctx.exception.code, 0)


class DryRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_dry_run_works_without_existing_file(self):
        audio = os.path.join(self.tmp, "missing.wav")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli.main([audio, "--dry-run"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Plan (dry run)", out)
        self.assertIn("missing_transcription.txt", out)
        self.assertIn("missing_fr.txt", out)

    def test_dry_run_imports_nothing_heavy(self):
        audio = os.path.join(self.tmp, "clip.wav")
        with redirect_stdout(io.StringIO()):
            cli.main([audio, "--dry-run"])
        self.assertNotIn("faster_whisper", sys.modules)
        self.assertNotIn("deep_translator", sys.modules)

    def test_dry_run_writes_nothing(self):
        audio = os.path.join(self.tmp, "clip.wav")
        with redirect_stdout(io.StringIO()):
            cli.main([audio, "--dry-run"])
        self.assertEqual(os.listdir(self.tmp), [])

    def test_model_flag_sets_env(self):
        audio = os.path.join(self.tmp, "clip.wav")
        os.environ.pop("WHISPER_MODEL", None)
        with redirect_stdout(io.StringIO()):
            cli.main([audio, "--dry-run", "--model", "tiny"])
        self.assertEqual(os.environ.get("WHISPER_MODEL"), "tiny")
        os.environ.pop("WHISPER_MODEL", None)


class MissingFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_missing_audio_exit_code_2(self):
        audio = os.path.join(self.tmp, "nope.wav")
        err = io.StringIO()
        with self.assertRaises(SystemExit) as ctx:
            with redirect_stderr(err):
                cli.main([audio])
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("not found", err.getvalue())


if __name__ == "__main__":
    unittest.main()
