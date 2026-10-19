"""Screenshot harness web server.

Serves the brs-engine browser simulator with the cross-origin isolation headers it
needs, plus the sideload zip at /app.zip, and forwards /api/* to the real LAN Media
server so the Roku app talks to genuine API responses, posters and byte ranges.

Headless Chromium ships without H.264, so WEBM_MAP can map a media id to a WebM copy
of the same clip for /stream only. This is a simulator workaround, not app behaviour.

    APP_ZIP=../../roku-client/out/roku-lan-media.zip UPSTREAM=http://127.0.0.1:8090 \
    WEBM_MAP=<media id>=/path/clip.webm uvicorn harness:app --port 8080
"""

import os

import httpx
from starlette.applications import Starlette
from starlette.responses import FileResponse, StreamingResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

HERE = os.path.dirname(os.path.abspath(__file__))
UPSTREAM = os.environ.get("UPSTREAM", "http://127.0.0.1:8090")
APP_ZIP = os.environ["APP_ZIP"]
WEBM = dict(item.split("=", 1) for item in os.environ.get("WEBM_MAP", "").split(",") if item)
FORWARD_REQUEST = {"range", "accept"}
FORWARD_RESPONSE = {"content-type", "content-length", "content-range", "accept-ranges", "cache-control"}

client = httpx.AsyncClient(base_url=UPSTREAM, timeout=30)


async def app_zip(request):
    return FileResponse(APP_ZIP)


async def api(request):
    parts = request.url.path.split("/")
    if len(parts) == 5 and parts[4] == "stream" and parts[3] in WEBM:
        return FileResponse(WEBM[parts[3]], media_type="video/webm")
    headers = {k: v for k, v in request.headers.items() if k.lower() in FORWARD_REQUEST}
    upstream = await client.send(client.build_request(request.method, request.url.path, headers=headers), stream=True)
    out = {k: v for k, v in upstream.headers.items() if k.lower() in FORWARD_RESPONSE}
    return StreamingResponse(upstream.aiter_raw(), status_code=upstream.status_code, headers=out)


class CrossOriginIsolation:
    """SharedArrayBuffer (used by the simulator) requires COOP/COEP."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                message["headers"] += [
                    (b"cross-origin-opener-policy", b"same-origin"),
                    (b"cross-origin-embedder-policy", b"require-corp"),
                    (b"cross-origin-resource-policy", b"same-origin"),
                ]
            await send(message)

        await self.app(scope, receive, send_with_headers)


app = CrossOriginIsolation(Starlette(routes=[
    Route("/app.zip", app_zip),
    Route("/api/{rest:path}", api, methods=["GET", "HEAD"]),
    Mount("/", StaticFiles(directory=os.path.join(HERE, "www"), html=True)),
]))
