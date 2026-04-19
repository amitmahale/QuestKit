from __future__ import annotations

from datetime import date, timedelta

from .models import ChildMemory, GameMode, MemorySuggestion, SessionResult, TopicProgress


class MemoryEngine:
    """Tracks learning signals and proposes spaced playful callbacks."""

    def __init__(self) -> None:
        self._memory_by_child: dict[str, ChildMemory] = {}

    def record_session(self, session: SessionResult) -> None:
        memory = self._memory_by_child.setdefault(session.child_id, ChildMemory(session.child_id))
        memory.sessions.append(session)

        progress = memory.topic_progress.setdefault(session.topic, TopicProgress(topic=session.topic))
        progress.update(
            score=session.score,
            hint_uses=session.hint_uses,
            completed_on=session.completed_on,
        )

    def get_progress(self, child_id: str) -> dict[str, TopicProgress]:
        memory = self._memory_by_child.get(child_id)
        if not memory:
            return {}
        return memory.topic_progress

    def suggest_callbacks(self, child_id: str, today: date | None = None) -> list[MemorySuggestion]:
        now = today or date.today()
        memory = self._memory_by_child.get(child_id)
        if not memory:
            return []

        suggestions: list[MemorySuggestion] = []
        for topic, progress in memory.topic_progress.items():
            if progress.last_seen is None:
                continue

            days_since = (now - progress.last_seen).days
            due_window = 2 <= days_since <= 5
            if not due_window:
                continue

            weak_topic = progress.avg_score < 0.65 or progress.avg_hint_uses >= 2.5
            mode = GameMode.QUICK_QUIZ if weak_topic else GameMode.MINI_CHALLENGE
            reason = (
                "Needs reinforcement after lower mastery signals."
                if weak_topic
                else "Ready for a confidence rematch to strengthen memory."
            )
            suggestions.append(
                MemorySuggestion(
                    child_id=child_id,
                    topic=topic,
                    suggested_mode=mode,
                    suggested_on=now + timedelta(days=1),
                    reason=reason,
                )
            )

        return sorted(suggestions, key=lambda s: s.topic)

    def adjacent_topic_suggestions(self, child_id: str) -> list[str]:
        memory = self._memory_by_child.get(child_id)
        if not memory:
            return []

        adjacency_map = {
            "moon phases": ["tides", "eclipses"],
            "ecosystems": ["food chains", "biomes"],
            "fractions": ["decimals", "ratios"],
            "ancient egypt": ["pyramids", "hieroglyphics"],
        }

        suggestions: list[str] = []
        for topic in memory.topic_progress:
            keys = adjacency_map.get(topic.lower(), [f"{topic} in daily life", f"{topic} challenge"])
            suggestions.extend(keys)

        seen = set()
        deduped = []
        for item in suggestions:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped[:6]
