"""Unit tests for transcribe_translate.core.

No real dependencies, no network, no model downloads. Heavy components are
replaced by injected fakes. These tests also implicitly confirm that the
module imports cleanly without faster-whisper / deep-translator installed.
"""

import os
import shutil
import sys
import tempfile
import unittest

from transcribe_translate import core


# --- Fakes ---------------------------------------------------------------


class FakeSegment:
    def __init__(self, text):
        self.text = text


class FakeInfo:
    def __init__(self, language, language_probability):
        self.language = language
        self.language_probability = language_probability


class FakeModel:
    """Stands in for faster_whisper.WhisperModel."""

    def __init__(self, segments, info):
        self._segments = segments
        self._info = info
        self.calls = []

    def transcribe(self, audio_path, **kwargs):
        self.calls.append((audio_path, kwargs))
        return iter(self._segments), self._info


class FakeTranslatorObject:
    def __init__(self, mapping=None, prefix="[fr] "):
        self.mapping = mapping or {}
        self.prefix = prefix
        self.seen = []

    def translate(self, text):
        self.seen.append(text)
        return self.mapping.get(text, self.prefix + text)


# --- ensure_ffmpeg -------------------------------------------------------


class EnsureFfmpegTests(unittest.TestCase):
    def test_present(self):
        # Should not raise when the lookup returns a path.
        core.ensure_ffmpeg(which=lambda name: "/usr/bin/ffmpeg")

    def test_missing_raises(self):
        with self.assertRaises(RuntimeError):
            core.ensure_ffmpeg(which=lambda name: None)


# --- transcribe_auto -----------------------------------------------------


class TranscribeAutoTests(unittest.TestCase):
    def test_concatenates_and_strips(self):
        model = FakeModel(
            [FakeSegment(" Hello"), FakeSegment(" world ")],
            FakeInfo("en", 0.97),
        )
        text, lang, prob = core.transcribe_auto("a.wav", model_loader=lambda: model)
        self.assertEqual(text, "Hello world")
        self.assertEqual(lang, "en")
        self.assertAlmostEqual(prob, 0.97)

    def test_passes_audio_path_to_model(self):
        model = FakeModel([FakeSegment("x")], FakeInfo("en", 1.0))
        core.transcribe_auto("clip.mp3", model_loader=lambda: model)
        self.assertEqual(model.calls[0][0], "clip.mp3")

    def test_uses_auto_language_options(self):
        model = FakeModel([FakeSegment("x")], FakeInfo("en", 1.0))
        core.transcribe_auto("clip.mp3", model_loader=lambda: model)
        kwargs = model.calls[0][1]
        self.assertIsNone(kwargs.get("language"))
        self.assertEqual(kwargs.get("task"), "transcribe")

    def test_missing_info_attrs_default(self):
        class BareInfo:
            pass

        model = FakeModel([FakeSegment("hi")], BareInfo())
        text, lang, prob = core.transcribe_auto("a.wav", model_loader=lambda: model)
        self.assertEqual(text, "hi")
        self.assertIsNone(lang)
        self.assertEqual(prob, 0.0)


# --- translate_text ------------------------------------------------------


class TranslateTextTests(unittest.TestCase):
    def test_object_translator(self):
        tr = FakeTranslatorObject({"hello": "bonjour"})
        self.assertEqual(core.translate_text("hello", translator=tr), "bonjour")
        self.assertEqual(tr.seen, ["hello"])

    def test_callable_translator(self):
        result = core.translate_text("hello", translator=lambda t: t.upper())
        self.assertEqual(result, "HELLO")

    def test_target_is_respected_by_object(self):
        # The object translator ignores target, but the call must succeed and
        # route through the object rather than importing deep_translator.
        tr = FakeTranslatorObject(prefix="[de] ")
        self.assertEqual(
            core.translate_text("hi", target="de", translator=tr), "[de] hi"
        )


# --- build_plan ----------------------------------------------------------


class BuildPlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_output_paths(self):
        audio = os.path.join(self.tmp, "speech.mp3")
        plan = core.build_plan(audio, target_lang="fr")
        self.assertEqual(
            plan["out_transcription"],
            os.path.join(self.tmp, "speech_transcription.txt"),
        )
        self.assertEqual(
            plan["out_translation"], os.path.join(self.tmp, "speech_fr.txt")
        )

    def test_target_lang_in_translation_name(self):
        audio = os.path.join(self.tmp, "speech.wav")
        plan = core.build_plan(audio, target_lang="es")
        self.assertTrue(plan["out_translation"].endswith("speech_es.txt"))

    def test_audio_exists_flag(self):
        audio = os.path.join(self.tmp, "speech.wav")
        plan = core.build_plan(audio)
        self.assertFalse(plan["audio_exists"])
        with open(audio, "wb") as handle:
            handle.write(b"\x00\x01")
        self.assertTrue(core.build_plan(audio)["audio_exists"])


# --- run -----------------------------------------------------------------


class RunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_end_to_end_with_fakes(self):
        audio = os.path.join(self.tmp, "clip.wav")
        with open(audio, "wb") as handle:
            handle.write(b"\x00")
        model = FakeModel(
            [FakeSegment("Bonjour"), FakeSegment(" le monde")],
            FakeInfo("fr", 0.99),
        )
        tr = FakeTranslatorObject({"Bonjour le monde": "Hello world"})
        result = core.run(
            audio,
            target_lang="en",
            model_loader=lambda: model,
            translator=tr,
        )
        self.assertEqual(result["text"], "Bonjour le monde")
        self.assertEqual(result["translation"], "Hello world")
        self.assertEqual(result["lang"], "fr")
        self.assertFalse(result["dry_run"])
        # Files written next to the audio.
        with open(result["out_transcription"], encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "Bonjour le monde")
        with open(result["out_translation"], encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "Hello world")

    def test_run_write_false_skips_files(self):
        audio = os.path.join(self.tmp, "clip.wav")
        with open(audio, "wb") as handle:
            handle.write(b"\x00")
        model = FakeModel([FakeSegment("hi")], FakeInfo("en", 1.0))
        result = core.run(
            audio,
            model_loader=lambda: model,
            translator=lambda t: t,
            write=False,
        )
        self.assertFalse(os.path.exists(result["out_transcription"]))
        self.assertFalse(os.path.exists(result["out_translation"]))

    def test_dry_run_returns_plan_and_writes_nothing(self):
        audio = os.path.join(self.tmp, "clip.wav")

        def exploding_loader():
            raise AssertionError("model loader must not run in dry-run")

        result = core.run(
            audio,
            target_lang="fr",
            dry_run=True,
            model_loader=exploding_loader,
        )
        self.assertTrue(result["dry_run"])
        self.assertIn("out_transcription", result)
        self.assertFalse(os.path.exists(result["out_transcription"]))
        self.assertFalse(os.path.exists(result["out_translation"]))


# --- import safety -------------------------------------------------------


class ImportSafetyTests(unittest.TestCase):
    def test_heavy_deps_absent_in_test_env(self):
        # The whole point: tests run without these installed. If this ever
        # fails it means the test environment changed, not that the package
        # is broken -- but we assert it so dry-run import-safety is meaningful.
        self.assertNotIn("faster_whisper", sys.modules)
        self.assertNotIn("deep_translator", sys.modules)


if __name__ == "__main__":
    unittest.main()
