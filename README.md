# QuestKit MVP Engine

QuestKit is a family learning engine that turns topics and excerpts into short, playable learning activities.

This repository implements an MVP-ready core service for:

- Child profile onboarding
- Mode-based activity generation (`quick_quiz`, `car_trivia`, `scavenger_hunt`, `mini_challenge`, `chapter_to_game`)
- Parent controls for tone, difficulty, duration, and chaos suppression
- Kid-friendly output with encouragement and adaptive hints
- Light memory loops with rematch suggestions in 2-5 days

## Quick start

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Example

```python
from questkit import (
    ChildProfile,
    FamilyStyle,
    GameMode,
    LearningService,
    GenerationRequest,
)

service = LearningService()
profile = ChildProfile(
    child_id="kid-1",
    name="Ava",
    age=10,
    reading_level="independent",
    favorite_topics=["space", "animals"],
    preferred_modes=[GameMode.CAR_TRIVIA],
    family_style=FamilyStyle.BALANCED,
)
service.register_child(profile)

request = GenerationRequest(
    child_id="kid-1",
    topic="Moon phases",
    mode=GameMode.CAR_TRIVIA,
    duration_minutes=8,
    difficulty=3,
    voice_enabled=True,
)
activity = service.generate_activity(request)
session = service.complete_activity(
    child_id="kid-1",
    activity_id=activity.activity_id,
    score=0.7,
    hint_uses=2,
)
```

## Design choices

The implementation follows the PRD's hybrid strategy:

- **Structured templates by mode** for consistency and quality.
- **Adaptive modifiers** (age, reading level, prior mastery, family style) for personalization.
- **Memory engine** to drive spaced re-exposure and topic adjacency.

This is intentionally deterministic and testable, making it a reliable backend foundation before adding full LLM content generation.
