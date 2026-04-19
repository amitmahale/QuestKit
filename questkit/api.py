from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .models import ChildProfile, FamilyStyle, GameMode, GenerationRequest
from .service import LearningService

WEB_ROOT = Path(__file__).resolve().parent.parent / "web"


class QuestKitAPI:
    """Thin JSON API around LearningService with in-memory state."""

    def __init__(self) -> None:
        self.service = LearningService()

    def register_child(self, payload: dict[str, Any]) -> dict[str, Any]:
        profile = ChildProfile(
            child_id=payload["child_id"],
            name=payload["name"],
            age=int(payload["age"]),
            reading_level=payload.get("reading_level", "independent"),
            favorite_topics=payload.get("favorite_topics", []),
            preferred_modes=[GameMode(m) for m in payload.get("preferred_modes", [GameMode.QUICK_QUIZ.value])],
            family_style=FamilyStyle(payload.get("family_style", FamilyStyle.BALANCED.value)),
            attention_span_minutes=int(payload.get("attention_span_minutes", 10)),
            calm_ui=bool(payload.get("calm_ui", True)),
        )
        self.service.register_child(profile)
        return {"ok": True, "child_id": profile.child_id}

    def generate_activity(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = GenerationRequest(
            child_id=payload["child_id"],
            topic=payload["topic"],
            mode=GameMode(payload["mode"]),
            duration_minutes=int(payload.get("duration_minutes", 8)),
            difficulty=int(payload.get("difficulty", 3)),
            source_text=payload.get("source_text"),
            solo_mode=bool(payload.get("solo_mode", False)),
            voice_enabled=bool(payload.get("voice_enabled", False)),
            educational_weight=float(payload.get("educational_weight", 0.5)),
            suppress_chaos=bool(payload.get("suppress_chaos", True)),
        )
        activity = self.service.generate_activity(request)
        return asdict(activity)

    def complete_activity(self, payload: dict[str, Any]) -> dict[str, Any]:
        session = self.service.complete_activity(
            child_id=payload["child_id"],
            activity_id=payload["activity_id"],
            score=float(payload["score"]),
            hint_uses=int(payload["hint_uses"]),
            completed_on=date.fromisoformat(payload["completed_on"]) if payload.get("completed_on") else None,
        )
        return asdict(session)

    def progress(self, child_id: str) -> dict[str, Any]:
        progress = self.service.get_progress(child_id)
        callbacks = self.service.get_callback_suggestions(child_id)
        adjacent = self.service.get_adjacent_topic_suggestions(child_id)
        return {
            "topics": {topic: asdict(stats) for topic, stats in progress.items()},
            "callbacks": [asdict(item) for item in callbacks],
            "adjacent": adjacent,
        }


def create_handler(api: QuestKitAPI):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/api/modes":
                self._send_json({"modes": [mode.value for mode in GameMode]})
                return
            if parsed.path == "/api/progress":
                child_id = parse_qs(parsed.query).get("child_id", [""])[0]
                if not child_id:
                    self._send_error("child_id is required", HTTPStatus.BAD_REQUEST)
                    return
                self._send_json(api.progress(child_id))
                return
            self._serve_static(parsed.path)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            payload = self._read_json_body()
            if payload is None:
                return
            try:
                if parsed.path == "/api/profile":
                    self._send_json(api.register_child(payload), status=HTTPStatus.CREATED)
                    return
                if parsed.path == "/api/activity":
                    self._send_json(api.generate_activity(payload), status=HTTPStatus.CREATED)
                    return
                if parsed.path == "/api/complete":
                    self._send_json(api.complete_activity(payload), status=HTTPStatus.CREATED)
                    return
                self._send_error("Unknown endpoint", HTTPStatus.NOT_FOUND)
            except (KeyError, ValueError) as exc:
                self._send_error(str(exc), HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

        def _read_json_body(self) -> dict[str, Any] | None:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length else b"{}"
            try:
                return json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_error("Body must be valid JSON", HTTPStatus.BAD_REQUEST)
                return None

        def _serve_static(self, raw_path: str) -> None:
            requested = raw_path.strip("/") or "index.html"
            file_path = (WEB_ROOT / requested).resolve()
            if WEB_ROOT not in file_path.parents and file_path != WEB_ROOT:
                self._send_error("Invalid path", HTTPStatus.BAD_REQUEST)
                return
            if not file_path.exists() or not file_path.is_file():
                self._send_error("Not found", HTTPStatus.NOT_FOUND)
                return

            content_type = "text/plain; charset=utf-8"
            if file_path.suffix == ".html":
                content_type = "text/html; charset=utf-8"
            elif file_path.suffix == ".js":
                content_type = "application/javascript; charset=utf-8"
            elif file_path.suffix == ".css":
                content_type = "text/css; charset=utf-8"

            body = file_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_error(self, message: str, status: HTTPStatus) -> None:
            self._send_json({"error": message}, status=status)

    return Handler


def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    api = QuestKitAPI()
    server = ThreadingHTTPServer((host, port), create_handler(api))
    print(f"QuestKit app running on http://{host}:{port}")
    server.serve_forever()
