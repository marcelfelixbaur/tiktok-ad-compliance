"""Tests for scripts/preflight_media.py. Skipped when ffmpeg isn't installed."""

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "skills" / "ad-compliance" / "scripts" / "preflight_media.py"


def make_video(path, audio):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=1080x1920:r=30:d=6"]
    if audio:
        cmd += ["-f", "lavfi", "-i", audio, "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "libx264", "-b:v", "2M", "-t", "6", str(path)]
    subprocess.run(cmd, check=True)


def preflight(path):
    r = subprocess.run([sys.executable, str(SCRIPT), str(path), "--platform", "tiktok", "--json"],
                       capture_output=True, text=True)
    return r.returncode, {c["name"]: c["status"] for c in json.loads(r.stdout)["checks"]}


class RequiredPlatform(unittest.TestCase):
    def test_platform_is_required(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "ad.mp4"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("ask the user", r.stderr)

    def test_unknown_platform_is_rejected(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "ad.mp4", "--platform", "meta"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg not installed")
class Audio(unittest.TestCase):
    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)

    def test_audible_track_passes(self):
        make_video(self.dir / "ok.mp4", "sine=f=440:d=6")
        code, checks = preflight(self.dir / "ok.mp4")
        self.assertEqual(code, 0)
        self.assertEqual(checks["audio level"], "PASS")

    def test_silent_track_fails(self):
        make_video(self.dir / "silent.mp4", "anullsrc=r=44100:cl=stereo")
        code, checks = preflight(self.dir / "silent.mp4")
        self.assertEqual(code, 1)
        self.assertEqual(checks["audio level"], "FAIL")

    def test_missing_track_fails(self):
        make_video(self.dir / "none.mp4", None)
        code, checks = preflight(self.dir / "none.mp4")
        self.assertEqual(code, 1)
        self.assertEqual(checks["audio present"], "FAIL")


if __name__ == "__main__":
    unittest.main()
