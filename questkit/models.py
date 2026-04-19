from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional


class FamilyStyle(str, Enum):
    CALM = "calm"
    BALANCED = "balanced"
    ENERGETIC = "energetic"


class GameMode(str, Enum):
    QUICK_QUIZ = "quick_quiz"
    CAR_TRIVIA = "car_trivia"
    SCAVENGER_HUNT = "scavenger_hunt"
    MINI_CHALLENGE = "mini_challenge"
    CHAPTER_TO_GAME = "chapter_to_game"


class SourceType(str, Enum):
    TOPIC = "topic"
    CHAPTER = "chapter"
    EXCERPT = "excerpt"


@dataclass
class ChildProfile:
    child_id: str
    name: str
    age: int
    reading_level: str
    favorite_topics: List[str]
    preferred_modes: List[GameMode]
    family_style: FamilyStyle
    attention_span_minutes: int = 10
    calm_ui: bool = True


@dataclass
class GenerationRequest:
    child_id: str
    topic: str
    mode: GameMode
    duration_minutes: int
    difficulty: int
    source_text: Optional[str] = None
    source_type: SourceType = SourceType.TOPIC
    solo_mode: bool = False
    voice_enabled: bool = False
    educational_weight: float = 0.5
    suppress_chaos: bool = True


@dataclass
class Question:
    prompt: str
    options: List[str]
    answer_index: int
    hint: str
    explanation: str


@dataclass
class Activity:
    activity_id: str
    child_id: str
    topic: str
    mode: GameMode
    title: str
    intro: str
    questions: List[Question]
    parent_notes: List[str]
    kid_encouragement: List[str]
    estimated_duration_minutes: int
    voice_script: Optional[List[str]] = None


@dataclass
class SessionResult:
    child_id: str
    activity_id: str
    topic: str
    mode: GameMode
    completed_on: date
    score: float
    hint_uses: int


@dataclass
class MemorySuggestion:
    child_id: str
    topic: str
    suggested_mode: GameMode
    suggested_on: date
    reason: str


@dataclass
class TopicProgress:
    topic: str
    attempts: int = 0
    avg_score: float = 0.0
    avg_hint_uses: float = 0.0
    last_seen: Optional[date] = None
    weak_signals: int = 0
    strong_signals: int = 0

    def update(self, score: float, hint_uses: int, completed_on: date) -> None:
        self.attempts += 1
        self.avg_score = ((self.avg_score * (self.attempts - 1)) + score) / self.attempts
        self.avg_hint_uses = (
            (self.avg_hint_uses * (self.attempts - 1)) + hint_uses
        ) / self.attempts
        self.last_seen = completed_on

        if score < 0.55 or hint_uses >= 3:
            self.weak_signals += 1
        elif score > 0.8 and hint_uses <= 1:
            self.strong_signals += 1


@dataclass
class ChildMemory:
    child_id: str
    sessions: List[SessionResult] = field(default_factory=list)
    topic_progress: dict[str, TopicProgress] = field(default_factory=dict)
