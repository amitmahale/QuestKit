const modeDescriptions = {
  quick_quiz: "Fast adaptive checks with kinder retries.",
  car_trivia: "Voice-friendly rounds for car rides and family play.",
  scavenger_hunt: "Movement clues that connect real spaces to concepts.",
  mini_challenge: "Short missions with timed rounds and streaks.",
  chapter_to_game: "Turn chapters/excerpts into mystery-like learning arcs."
};

const output = document.getElementById("output");
const modeGrid = document.getElementById("mode-grid");
const modeSelect = document.getElementById("mode-select");
const modeDescription = document.getElementById("mode-description");

const writeOutput = (label, data) => {
  output.textContent = `${label}\n${JSON.stringify(data, null, 2)}`;
};

const request = async (path, options = {}) => {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error || `Request failed (${response.status})`);
  }
  return body;
};

const setActiveMode = (mode) => {
  modeDescription.textContent = modeDescriptions[mode] || "";
  document.querySelectorAll(".card[data-mode]").forEach((card) => {
    card.classList.toggle("active", card.dataset.mode === mode);
  });
  modeSelect.value = mode;
};

const mountModes = (modes) => {
  modeGrid.innerHTML = "";
  modeSelect.innerHTML = "";
  modes.forEach((mode, index) => {
    const card = document.createElement("article");
    card.className = `card${index === 0 ? " active" : ""}`;
    card.setAttribute("role", "button");
    card.setAttribute("tabindex", "0");
    card.dataset.mode = mode;
    card.innerHTML = `<strong>${mode.replaceAll("_", " ")}</strong><p class="muted">${modeDescriptions[mode] || ""}</p>`;
    card.addEventListener("click", () => setActiveMode(mode));
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        setActiveMode(mode);
      }
    });
    modeGrid.append(card);

    const option = document.createElement("option");
    option.value = mode;
    option.textContent = mode;
    modeSelect.append(option);
  });
  setActiveMode(modes[0]);
};

const formDataJson = (form) => Object.fromEntries(new FormData(form).entries());

document.getElementById("profile-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const data = formDataJson(event.currentTarget);
    const payload = {
      ...data,
      age: Number(data.age),
      favorite_topics: [],
      preferred_modes: [modeSelect.value],
      family_style: "balanced",
    };
    const res = await request("/api/profile", { method: "POST", body: JSON.stringify(payload) });
    document.getElementById("profile-status").textContent = `Registered ${res.child_id}`;
    writeOutput("Child registered", res);
  } catch (err) {
    writeOutput("Error", { message: err.message });
  }
});

document.getElementById("activity-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const data = formDataJson(event.currentTarget);
    const payload = {
      ...data,
      duration_minutes: Number(data.duration_minutes),
      difficulty: Number(data.difficulty),
      voice_enabled: true,
      suppress_chaos: true,
    };
    const res = await request("/api/activity", { method: "POST", body: JSON.stringify(payload) });
    document.getElementById("activity-id").value = res.activity_id;
    writeOutput("Activity generated", res);
  } catch (err) {
    writeOutput("Error", { message: err.message });
  }
});

document.getElementById("complete-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const data = formDataJson(event.currentTarget);
    const payload = {
      ...data,
      score: Number(data.score),
      hint_uses: Number(data.hint_uses),
    };
    const res = await request("/api/complete", { method: "POST", body: JSON.stringify(payload) });
    writeOutput("Session completed", res);
  } catch (err) {
    writeOutput("Error", { message: err.message });
  }
});

document.getElementById("progress-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const data = formDataJson(event.currentTarget);
    const res = await request(`/api/progress?child_id=${encodeURIComponent(data.child_id)}`);
    writeOutput("Progress snapshot", res);
  } catch (err) {
    writeOutput("Error", { message: err.message });
  }
});

request("/api/modes")
  .then(({ modes }) => mountModes(modes))
  .catch((err) => writeOutput("Error", { message: err.message }));
