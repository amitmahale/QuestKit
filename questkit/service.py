from __future__ import annotations

from datetime import date

from .engine import ActivityEngine
from .memory import MemoryEngine
from .models import (
    Activity,
    ChildProfile,
    GenerationRequest,
    MemorySuggestion,
    SessionResult,
    TopicProgress,
)


class LearningService:
    """High-level orchestration service for QuestKit MVP flows."""

    def __init__(self) -> None:
        self._profiles: dict[str, ChildProfile] = {}
        self._activities: dict[str, Activity] = {}
        self._engine = ActivityEngine()
        self._memory = MemoryEngine()

    def register_child(self, profile: ChildProfile) -> None:
        self._profiles[profile.child_id] = profile

    def get_child(self, child_id: str) -> ChildProfile:
        if child_id not in self._profiles:
            raise KeyError(f"Unknown child_id: {child_id}")
        return self._profiles[child_id]

    def generate_activity(self, request: GenerationRequest) -> Activity:
        profile = self.get_child(request.child_id)
        activity = self._engine.generate(profile, request)
        self._activities[activity.activity_id] = activity
        return activity

    def complete_activity(
        self,
        child_id: str,
        activity_id: str,
        score: float,
        hint_uses: int,
        completed_on: date | None = None,
    ) -> SessionResult:
        if activity_id not in self._activities:
            raise KeyError(f"Unknown activity_id: {activity_id}")

        activity = self._activities[activity_id]
        if activity.child_id != child_id:
            raise ValueError("Activity does not belong to child")

        session = SessionResult(
            child_id=child_id,
            activity_id=activity_id,
            topic=activity.topic,
            mode=activity.mode,
            completed_on=completed_on or date.today(),
            score=score,
            hint_uses=hint_uses,
        )
        self._memory.record_session(session)
        return session

    def get_progress(self, child_id: str) -> dict[str, TopicProgress]:
        return self._memory.get_progress(child_id)

    def get_callback_suggestions(
        self,
        child_id: str,
        today: date | None = None,
    ) -> list[MemorySuggestion]:
        return self._memory.suggest_callbacks(child_id, today=today)

    def get_adjacent_topic_suggestions(self, child_id: str) -> list[str]:
        return self._memory.adjacent_topic_suggestions(child_id)
