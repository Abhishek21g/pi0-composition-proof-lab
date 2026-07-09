const SCENARIOS = [
  {
    file: "airfryer-receipt.json",
    label: "π0.7 · air fryer",
    subtitle: "COACH_REQUIRED",
    insight:
      "PI found only tangential training episodes (close air fryer, Franka DROID). Zero-shot fails; step-by-step coaching succeeds — the central π0.7 evaluation problem.",
  },
];

let activeFile = SCENARIOS[0].file;

function dataUrl(file) {
  if (window.EMBEDDED_DEMOS && window.EMBEDDED_DEMOS[file]) {
    return null;
  }
  const base = window.location.pathname.replace(/\/index\.html$/, "").replace(/\/?$/, "/");
  return `${base}data/${file}`;
}

async function loadReceipt(file) {
  if (window.EMBEDDED_DEMOS && window.EMBEDDED_DEMOS[file]) {
    return window.EMBEDDED_DEMOS[file];
  }
  const res = await fetch(dataUrl(file));
  if (!res.ok) throw new Error(`Failed to load ${file}`);
  return res.json();
}

function verdictClass(verdict) {
  if (verdict === "COMPOSE") return "pass";
  if (verdict === "NO_GO") return "fail";
  return "fail";
}

function renderDoctors(doctors) {
  const el = document.getElementById("doctorList");
  el.innerHTML = doctors
    .map(
      (d) => `
      <li class="doctor-item">
        <span class="badge ${d.passed ? "pass" : "fail"}">${d.passed ? "PASS" : "FAIL"}</span>
        <div>
          <strong>${d.name}</strong>
          <div class="match-meta">${d.detail}</div>
        </div>
        <span>${d.score.toFixed(2)}</span>
      </li>`
    )
    .join("");
}

function renderMatches(matches) {
  const el = document.getElementById("matchList");
  const top = matches.slice(0, 6);
  el.innerHTML = top
    .map(
      (m) => `
      <li class="match-item">
        <span class="badge pass">${m.score.toFixed(2)}</span>
        <div>
          <strong>${m.skill_id}</strong> → <code>${m.episode_id}</code>
          <div class="match-meta">${m.robot} · ${m.instruction}</div>
        </div>
      </li>`
    )
    .join("");
}

function renderTangential(ids) {
  const el = document.getElementById("tangentialList");
  el.innerHTML = ids
    .map((id) => `<li class="match-item"><span class="badge fail">tangential</span><div><code>${id}</code></div></li>`)
    .join("");
}

async function renderScenario(file) {
  const receipt = await loadReceipt(file);
  const scenario = SCENARIOS.find((s) => s.file === file);

  document.getElementById("heroVerdict").textContent = receipt.verdict;
  document.getElementById("heroVerdict").className = "verdict-pill";
  document.getElementById("heroRunId").textContent = receipt.run_id;
  document.getElementById("heroCoaching").textContent = receipt.coaching_required ? "yes" : "no";
  document.getElementById("heroTangential").textContent = String(receipt.tangential_episodes.length);
  document.getElementById("dashVerdict").textContent = receipt.verdict;
  document.getElementById("dashTask").textContent = receipt.task;
  document.getElementById("insight").textContent = scenario?.insight || "";

  renderDoctors(receipt.doctors);
  renderMatches(receipt.skill_matches);
  renderTangential(receipt.tangential_episodes);
}

function bindScenarioButtons() {
  const list = document.getElementById("scenarioList");
  list.innerHTML = SCENARIOS.map(
    (s) => `
    <button class="scenario-btn ${s.file === activeFile ? "active" : ""}" data-file="${s.file}">
      ${s.label}
      <span>${s.subtitle}</span>
    </button>`
  ).join("");

  list.querySelectorAll(".scenario-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      activeFile = btn.dataset.file;
      bindScenarioButtons();
      await renderScenario(activeFile);
    });
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  bindScenarioButtons();
  await renderScenario(activeFile);
});
