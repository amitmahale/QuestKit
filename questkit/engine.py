from __future__ import annotations

from dataclasses import dataclass
from hashlib import md5
import re
from typing import List

from .models import Activity, ChildProfile, GameMode, GenerationRequest, Question


@dataclass
class GenerationContext:
    difficulty: int
    question_count: int
    energy_level: str
    source_facts: list[str]


class ActivityEngine:
    """Template-driven activity generation with light personalization."""

    def generate(self, profile: ChildProfile, request: GenerationRequest) -> Activity:
        ctx = self._build_context(profile, request)
        questions = self._build_questions(request, ctx)
        activity_id = self._activity_id(profile.child_id, request.topic, request.mode.value)

        intro = self._intro_for_mode(request.mode, request.topic, profile.name)
        parent_notes = self._parent_notes(request, ctx)
        encouragement = self._kid_encouragement(ctx.energy_level, request.suppress_chaos)

        voice_script = None
        if request.voice_enabled:
            voice_script = self._voice_script(intro, questions)

        return Activity(
            activity_id=activity_id,
            child_id=profile.child_id,
            topic=request.topic,
            mode=request.mode,
            title=self._title_for_mode(request.mode, request.topic),
            intro=intro,
            questions=questions,
            parent_notes=parent_notes,
            kid_encouragement=encouragement,
            estimated_duration_minutes=request.duration_minutes,
            voice_script=voice_script,
        )

    def _build_context(self, profile: ChildProfile, request: GenerationRequest) -> GenerationContext:
        base_count = max(4, min(12, request.duration_minutes + 2))

        if request.mode == GameMode.CHAPTER_TO_GAME:
            base_count = max(base_count, 6)
        elif request.mode == GameMode.SCAVENGER_HUNT:
            base_count = max(5, min(8, request.duration_minutes))

        if profile.age <= 8:
            difficulty = max(1, request.difficulty - 1)
        elif profile.age >= 11:
            difficulty = min(5, request.difficulty + 1)
        else:
            difficulty = request.difficulty

        if profile.reading_level.lower() in {"emerging", "early"}:
            difficulty = max(1, difficulty - 1)

        energy_level = profile.family_style.value
        if request.suppress_chaos:
            energy_level = "calm"

        source_facts = self._extract_source_facts(request)
        if request.educational_weight >= 0.8 and source_facts:
            base_count = min(14, base_count + 1)

        return GenerationContext(
            difficulty=difficulty,
            question_count=base_count,
            energy_level=energy_level,
            source_facts=source_facts,
        )

    def _build_questions(self, request: GenerationRequest, ctx: GenerationContext) -> List[Question]:
        prompts = {
            GameMode.QUICK_QUIZ: "Quick check",
            GameMode.CAR_TRIVIA: "Road question",
            GameMode.SCAVENGER_HUNT: "Find and explain",
            GameMode.MINI_CHALLENGE: "Challenge card",
            GameMode.CHAPTER_TO_GAME: "Story mystery",
        }
        prompt_prefix = prompts[request.mode]

        questions: List[Question] = []
        for idx in range(1, ctx.question_count + 1):
            source_fact = ctx.source_facts[(idx - 1) % len(ctx.source_facts)] if ctx.source_facts else None
            stem = self._question_stem(prompt_prefix, idx, request.topic, source_fact, request.solo_mode)
            options = self._options_for_question(idx, request.topic, source_fact)

            hint = self._hint_for_mode(request.mode, request.topic, idx)
            explanation = (
                f"This connects {request.topic} to a real-world example and reinforces"
                " recall through short repetition."
            )
            if source_fact:
                explanation = f"Anchor fact: {source_fact}. " + explanation
            questions.append(
                Question(
                    prompt=stem,
                    options=options,
                    answer_index=0,
                    hint=hint,
                    explanation=explanation,
                )
            )

        return questions

    def _question_stem(
        self,
        prompt_prefix: str,
        idx: int,
        topic: str,
        source_fact: str | None,
        solo_mode: bool,
    ) -> str:
        if source_fact:
            if solo_mode:
                return (
                    f"{prompt_prefix} {idx}: Read this clue — '{source_fact}'. "
                    f"What does it teach you about {topic}?"
                )
            return (
                f"{prompt_prefix} {idx}: Using the clue '{source_fact}', "
                f"share one key idea about {topic}."
            )

        if solo_mode:
            return f"{prompt_prefix} {idx}: On your own, explain one key idea about {topic}."
        return f"{prompt_prefix} {idx}: What is one key idea about {topic}?"

    def _options_for_question(self, idx: int, topic: str, source_fact: str | None) -> list[str]:
        if source_fact:
            return [
                f"It matches this fact: {source_fact}",
                f"It says the opposite of the clue",
                f"It is unrelated to {topic}",
                f"It is just a random guess",
            ]
        return [
            f"Core concept #{idx}",
            f"Trick answer #{idx}",
            f"Related detail #{idx}",
            f"Wild guess #{idx}",
        ]

    def _hint_for_mode(self, mode: GameMode, topic: str, idx: int) -> str:
        if mode == GameMode.CAR_TRIVIA:
            return f"Think of a simple fact about {topic} you can say in one sentence."
        if mode == GameMode.SCAVENGER_HUNT:
            return f"Look around your space for something linked to {topic} and describe why."
        if mode == GameMode.CHAPTER_TO_GAME:
            return f"Use a clue from the chapter to unlock mystery step {idx}."
        return f"Break {topic} into who/what/why for easier recall."

    def _title_for_mode(self, mode: GameMode, topic: str) -> str:
        names = {
            GameMode.QUICK_QUIZ: "Quick Quiz",
            GameMode.CAR_TRIVIA: "Car Trivia",
            GameMode.SCAVENGER_HUNT: "Scavenger Hunt",
            GameMode.MINI_CHALLENGE: "Mini Challenge",
            GameMode.CHAPTER_TO_GAME: "Chapter-to-Game Mystery",
        }
        return f"{names[mode]}: {topic}"

    def _intro_for_mode(self, mode: GameMode, topic: str, child_name: str) -> str:
        intros = {
            GameMode.QUICK_QUIZ: f"{child_name}, ready for a 5-minute brain boost on {topic}?",
            GameMode.CAR_TRIVIA: f"Seatbelts on! Let's play lightning trivia about {topic}.",
            GameMode.SCAVENGER_HUNT: f"Quest time! Find clues around you tied to {topic}.",
            GameMode.MINI_CHALLENGE: f"Mini challenge unlocked: beat these {topic} rounds.",
            GameMode.CHAPTER_TO_GAME: f"Turn the chapter into a mystery mission about {topic}.",
        }
        return intros[mode]

    def _parent_notes(self, request: GenerationRequest, ctx: GenerationContext) -> list[str]:
        notes = [
            f"Difficulty calibrated to {ctx.difficulty}/5.",
            f"Estimated rounds: {ctx.question_count}.",
            (
                "Pacing is calm with reduced randomness."
                if request.suppress_chaos
                else "Pacing includes surprise variation."
            ),
            (
                "Output favors educational depth."
                if request.educational_weight >= 0.5
                else "Output favors playful momentum."
            ),
        ]
        if ctx.source_facts:
            notes.append(f"Using {len(ctx.source_facts)} source-based clue(s) from provided text.")
        if request.solo_mode:
            notes.append("Prompts are phrased for independent play.")
        return notes

    def _kid_encouragement(self, energy_level: str, calm: bool) -> list[str]:
        if calm:
            return [
                "Great thinking.",
                "Take your time—you've got this.",
                "Every round helps your brain grow.",
            ]

        if energy_level == "energetic":
            return ["Boom! Nice answer!", "Level up!", "Quest streak activated!"]

        return ["Nice work!", "Keep going!", "You're building a strong memory trail."]

    def _voice_script(self, intro: str, questions: list[Question]) -> list[str]:
        script = [intro]
        for q in questions:
            script.append(q.prompt)
            script.append(f"Hint if needed: {q.hint}")
        script.append("Amazing effort. Want a remix round?")
        return script

    def _activity_id(self, child_id: str, topic: str, mode: str) -> str:
        digest = md5(f"{child_id}:{topic}:{mode}".encode("utf-8")).hexdigest()[:12]
        return f"act_{digest}"

    def _extract_source_facts(self, request: GenerationRequest) -> list[str]:
        if not request.source_text:
            return []

        fragments = re.split(r"[.!?\n]+", request.source_text)
        cleaned = [segment.strip() for segment in fragments if segment.strip()]
        if not cleaned:
            return []
        return cleaned[:6]
