const state = {
  topic: "Space",
  mode: "Quick Quiz",
  age: "6-8",
};

const groupButtons = document.querySelectorAll(".option-row .choice");
const resultEl = document.getElementById("module-result");

groupButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    const row = btn.closest(".option-row");
    const group = row.dataset.group;
    row.querySelectorAll(".choice").forEach((choice) => choice.classList.remove("active"));
    btn.classList.add("active");
    state[group] = btn.dataset.value;
  });
});

const quests = {
  "Quick Quiz": "Ask 5 rapid-fire questions",
  "Car Trivia": "Play 3 spoken rounds during a drive",
  "Chapter Game": "Turn one reading chapter into clues",
};

const challengeByAge = {
  "6-8": "Use picture hints and two-answer choices.",
  "9-11": "Add one bonus challenge card at the end.",
  "12-14": "Add timer pressure and one puzzle clue.",
};

document.getElementById("build-module")?.addEventListener("click", () => {
  const questLine = quests[state.mode] || "Create a mini learning activity";
  const ageGuide = challengeByAge[state.age] || "Keep the activity short and fun.";
  resultEl.innerHTML = `
    <b>${state.topic} • ${state.mode} • Age ${state.age}</b><br/>
    1) ${questLine} about <b>${state.topic}</b>.<br/>
    2) Let the child earn 1 badge for every correct answer.<br/>
    3) Finish with a "family high-five" recap.<br/>
    <i>Tip:</i> ${ageGuide}
  `;
});
