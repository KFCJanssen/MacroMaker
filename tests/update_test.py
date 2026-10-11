"""
Windows test of the self-update mechanism, run by GitHub Actions.
Starts the latest *released* MacroMaker.exe, replaces it *while it is running*
with the freshly built dist/MacroMaker.exe using updater.download_and_install(),
launches the new copy with --after-update, closes the old one and checks the
new copy takes over.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import updater  # noqa: E402

info = updater.check_latest()
assert info["url"], "latest release has no MacroMaker.exe asset"
print("latest release:", info["version"])

work = tempfile.mkdtemp()
exe = os.path.join(work, "MacroMaker.exe")
import pathlib  # noqa: E402
import urllib.request  # noqa: E402
urllib.request.urlretrieve(info["url"], exe)
new_build = pathlib.Path(ROOT, "dist", "MacroMaker.exe")
assert new_build.exists(), "build dist/MacroMaker.exe first"


def kill_tree(proc):
    subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                   capture_output=True)

old_proc = subprocess.Popen([exe])
time.sleep(8)
assert old_proc.poll() is None, "old exe did not start"

# Pretend we are that exe and update it while it runs
sys.executable = exe
sys.frozen = True
fractions = []
new_path = updater.download_and_install(new_build.as_uri(), fractions.append)
assert new_path == exe and os.path.exists(exe), "new exe not in place"
assert os.path.exists(exe + ".old"), "old exe was not renamed"
assert fractions and fractions[-1] > 0.99, "no download progress reported"

new_proc = updater.launch_new(exe)
time.sleep(3)
kill_tree(old_proc)                  # the old copy quits
time.sleep(10)
assert new_proc.poll() is None, "new copy did not take over after the old one quit"
kill_tree(new_proc)
time.sleep(2)
shutil.rmtree(work, ignore_errors=True)
print("update test passed")
