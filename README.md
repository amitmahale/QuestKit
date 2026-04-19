# QuestKit Full MVP App

QuestKit is now a working end-to-end app with:

- **Backend API** for child registration, activity generation, completion tracking, and memory callbacks.
- **Interactive frontend** for running the full loop in-browser.
- **Core learning engine** with adaptive generation + spaced callback logic.

## Run locally

```bash
python -m questkit
```

Then open `http://localhost:8000`.

## API Endpoints

- `GET /api/modes`
- `POST /api/profile`
- `POST /api/activity`
- `POST /api/complete`
- `GET /api/progress?child_id=...`

## Test

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Notes

All data is in-memory for MVP speed and clarity. Restarting the server resets session/profile state.
