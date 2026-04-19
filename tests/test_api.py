import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from questkit.api import QuestKitAPI, create_handler


class QuestKitAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(QuestKitAPI()))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.host, self.port = self.server.server_address

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)

    def _request(self, method: str, path: str, payload: dict | None = None):
        conn = HTTPConnection(self.host, self.port, timeout=5)
        headers = {"Content-Type": "application/json"}
        body = json.dumps(payload) if payload is not None else None
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        raw = response.read().decode("utf-8")
        conn.close()
        return response.status, json.loads(raw)

    def test_full_flow_endpoints(self) -> None:
        status, data = self._request("GET", "/api/modes")
        self.assertEqual(status, 200)
        self.assertIn("quick_quiz", data["modes"])

        status, data = self._request(
            "POST",
            "/api/profile",
            {
                "child_id": "kid-1",
                "name": "Ava",
                "age": 10,
                "reading_level": "independent",
                "favorite_topics": ["space"],
                "preferred_modes": ["quick_quiz"],
                "family_style": "balanced",
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(data["child_id"], "kid-1")

        status, activity = self._request(
            "POST",
            "/api/activity",
            {
                "child_id": "kid-1",
                "topic": "Moon phases",
                "mode": "car_trivia",
                "duration_minutes": 8,
                "difficulty": 3,
                "voice_enabled": True,
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(activity["mode"], "car_trivia")

        status, _ = self._request(
            "POST",
            "/api/complete",
            {
                "child_id": "kid-1",
                "activity_id": activity["activity_id"],
                "score": 0.7,
                "hint_uses": 1,
            },
        )
        self.assertEqual(status, 201)

        status, progress = self._request("GET", "/api/progress?child_id=kid-1")
        self.assertEqual(status, 200)
        self.assertIn("Moon phases", progress["topics"])


if __name__ == "__main__":
    unittest.main()
