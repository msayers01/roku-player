"""Drive the real Roku app in the browser simulator with remote-key presses and save screenshots.

Usage: python capture.py <origin, e.g. http://192.0.2.2:8080> <server ip to type> <output dir>
Requires Playwright with Chromium (CHROMIUM env var to override the executable).
"""

import json
import os
import sys
import tempfile
import time

from playwright.sync_api import sync_playwright

ORIGIN, SERVER_IP, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
CHROMIUM = os.environ.get("CHROMIUM")


# brs-engine keeps the simulated registry in localStorage as "<developerId>.<section>.<key>".
DEVELOPER_ID = "34c6fceca75e456f25e7e99531e2425c6c1de443"


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    # The simulator's keyboard dialog drops scripted key presses unpredictably, so only the
    # first-run shots go through it; the other sessions start with the address already saved
    # in the registry, as on a Roku that has connected before.
    with sync_playwright() as p:
        session(p, first_run, registry=None)
        session(p, walkthrough, registry={"host": SERVER_IP, "port": "8080"})
        session(p, server_offline, registry={"host": SERVER_IP, "port": "9999"})


def session(p, script, registry) -> None:
    browser = p.chromium.launch(
        executable_path=CHROMIUM,
        args=[f"--unsafely-treat-insecure-origin-as-secure={ORIGIN}", "--autoplay-policy=no-user-gesture-required"],
    )
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    if registry:
        items = {f"{DEVELOPER_ID}.LanMedia.{k}": v for k, v in registry.items()}
        page.add_init_script(f"for (const [k, v] of Object.entries({json.dumps(items)})) localStorage.setItem(k, v);")
    console = open(os.path.join(tempfile.gettempdir(), f"lan-media-{script.__name__}.log"), "w")
    page.on("console", lambda msg: console.write(msg.text + "\n"))
    page.goto(ORIGIN + "/")
    time.sleep(9)
    script(Remote(page))
    browser.close()


class Remote:
    def __init__(self, page):
        self.page = page

    def key(self, name: str, wait: float = 0.5, times: int = 1) -> None:
        for _ in range(times):
            self.page.evaluate(f"brs.sendKeyPress({name!r})")
            time.sleep(wait)

    def type(self, text: str) -> None:
        for ch in text:
            self.key("lit_" + ch, 0.25)

    def snap(self, name: str) -> None:
        self.page.screenshot(path=os.path.join(OUT, f"{name}.png"))
        print("saved", name, flush=True)


def first_run(r: Remote) -> None:
    r.snap("01-connection")
    r.key("select", 1.5)                     # Server IP -> keyboard
    r.type(SERVER_IP)
    time.sleep(0.5)
    r.snap("02-ip-keyboard")


def walkthrough(r: Remote) -> None:
    time.sleep(6)                            # auto-connect with the saved address
    r.key("right", 1.2)
    r.snap("03-library")

    r.key("down", 0.4); r.key("right", 0.4, 4); r.key("select", 3)   # Velvet Static (MPEG-4 Part 2)
    r.snap("05-details-unsupported")
    r.key("back", 1.5)
    r.key("up", 0.4); r.key("left", 0.4, 5); r.key("select", 3)      # Aurora Drift
    r.snap("04-details")

    r.key("select", 3.5)                     # Play; HUD shows briefly at start
    r.snap("06-playback-start")
    time.sleep(24)
    r.key("select", 0.8)                     # show HUD
    r.key("select", 1.5)                     # Pause
    r.snap("07-paused-hud")
    r.key("right", 0.5); r.key("select", 1.0)    # +15s while paused
    r.snap("08-skip-forward-15")
    r.key("left", 0.5, 2); r.key("select", 1.0)  # -15s
    r.snap("09-rewind-15")
    r.key("right", 0.4, 3); r.key("select", 1)   # Audio
    r.snap("10-audio-eq-notice")

    r.key("back", 0.6)                       # close panel
    r.key("back", 0.6)                       # hide HUD
    r.key("back", 2)                         # leave playback
    r.key("back", 1.5)                       # leave details
    r.key("info", 1.5)                       # * = server settings
    r.snap("11-settings")


def server_offline(r: Remote) -> None:
    time.sleep(8)                            # saved port has nothing listening
    r.snap("12-connection-error")


if __name__ == "__main__":
    main()
