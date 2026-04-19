from datetime import date
import unittest

from questkit import (
    ChildProfile,
    FamilyStyle,
    GameMode,
    GenerationRequest,
    LearningService,
    SourceType,
)


class LearningServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = LearningService()
        self.profile = ChildProfile(
            child_id="kid-1",
            name="Ava",
            age=10,
            reading_level="independent",
            favorite_topics=["space"],
            preferred_modes=[GameMode.CAR_TRIVIA],
            family_style=FamilyStyle.BALANCED,
            attention_span_minutes=10,
            calm_ui=True,
        )
        self.service.register_child(self.profile)

    def test_generates_car_trivia_activity_with_voice_script(self) -> None:
        request = GenerationRequest(
            child_id="kid-1",
            topic="Moon phases",
            mode=GameMode.CAR_TRIVIA,
            duration_minutes=8,
            difficulty=3,
            voice_enabled=True,
            suppress_chaos=True,
        )
        activity = self.service.generate_activity(request)

        self.assertEqual(activity.child_id, "kid-1")
        self.assertEqual(activity.mode, GameMode.CAR_TRIVIA)
        self.assertTrue(len(activity.questions) >= 8)
        self.assertIsNotNone(activity.voice_script)
        self.assertIn("calm", " ".join(activity.parent_notes).lower())

    def test_records_progress_and_suggests_callback_in_due_window(self) -> None:
        request = GenerationRequest(
            child_id="kid-1",
            topic="Ecosystems",
            mode=GameMode.QUICK_QUIZ,
            duration_minutes=5,
            difficulty=2,
        )
        activity = self.service.generate_activity(request)
        self.service.complete_activity(
            child_id="kid-1",
            activity_id=activity.activity_id,
            score=0.4,
            hint_uses=4,
            completed_on=date(2026, 4, 15),
        )

        progress = self.service.get_progress("kid-1")
        self.assertIn("Ecosystems", progress)
        self.assertEqual(progress["Ecosystems"].attempts, 1)
        self.assertGreaterEqual(progress["Ecosystems"].weak_signals, 1)

        suggestions = self.service.get_callback_suggestions("kid-1", today=date(2026, 4, 19))
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].topic, "Ecosystems")
        self.assertEqual(suggestions[0].suggested_mode, GameMode.QUICK_QUIZ)

    def test_adjacent_topic_suggestions(self) -> None:
        request = GenerationRequest(
            child_id="kid-1",
            topic="Moon phases",
            mode=GameMode.MINI_CHALLENGE,
            duration_minutes=6,
            difficulty=3,
        )
        activity = self.service.generate_activity(request)
        self.service.complete_activity(
            child_id="kid-1",
            activity_id=activity.activity_id,
            score=0.9,
            hint_uses=0,
            completed_on=date(2026, 4, 17),
        )

        adjacent = self.service.get_adjacent_topic_suggestions("kid-1")
        self.assertIn("tides", adjacent)
        self.assertIn("eclipses", adjacent)

    def test_source_text_is_used_for_question_prompts(self) -> None:
        request = GenerationRequest(
            child_id="kid-1",
            topic="Volcanoes",
            mode=GameMode.CHAPTER_TO_GAME,
            duration_minutes=6,
            difficulty=3,
            source_type=SourceType.EXCERPT,
            source_text="Magma rises through cracks. Pressure builds before eruption.",
            solo_mode=True,
            educational_weight=0.9,
        )
        activity = self.service.generate_activity(request)

        self.assertTrue(any("Magma rises through cracks" in q.prompt for q in activity.questions))
        self.assertTrue(any("independent play" in note.lower() for note in activity.parent_notes))
        self.assertTrue(any("source-based clue" in note.lower() for note in activity.parent_notes))

    def test_validates_activity_completion_inputs(self) -> None:
        request = GenerationRequest(
            child_id="kid-1",
            topic="Fractions",
            mode=GameMode.QUICK_QUIZ,
            duration_minutes=5,
            difficulty=2,
        )
        activity = self.service.generate_activity(request)

        with self.assertRaises(ValueError):
            self.service.complete_activity(
                child_id="kid-1",
                activity_id=activity.activity_id,
                score=1.3,
                hint_uses=0,
            )

        with self.assertRaises(ValueError):
            self.service.complete_activity(
                child_id="kid-1",
                activity_id=activity.activity_id,
                score=0.7,
                hint_uses=-1,
            )


if __name__ == "__main__":
    unittest.main()
