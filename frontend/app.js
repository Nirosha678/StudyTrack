
const BASE_URL = "";


const errorBanner = document.getElementById("error-banner");

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.hidden = false;
}

function hideError() {
  errorBanner.hidden = true;
  errorBanner.textContent = "";
}


async function apiFetch(path, options = {}) {
  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, options);
  } catch (networkError) {
   
    throw new Error("Could not reach the StudyTrack backend. Is the server running?");
  }

  if (!response.ok) {
    let detail = `Request failed (HTTP ${response.status})`;
    try {
      const body = await response.json();
      if (body.detail) detail = body.detail;
    } catch (_) {
      
    }
    throw new Error(detail);
  }

  // 204 No Content has no JSON body to parse
  if (response.status === 204) return null;
  return response.json();
}

// =============================================================================
// Roster: load, render, add, edit age, delete
// =============================================================================

const rosterList = document.getElementById("roster-list"); 
const rosterCards = document.getElementById("roster-cards"); 
function createStudentCard(student) {
  const card = document.createElement("article");
  card.className = "student-card";
  card.dataset.id = student.id; 

  const name = document.createElement("h3");
  name.textContent = student.name;

  const email = document.createElement("p");
  email.className = "email";
  email.textContent = student.email;

  const ageRow = document.createElement("div");
  ageRow.className = "age-row";

  const ageLabel = document.createElement("span");
  ageLabel.className = "age-display";
  ageLabel.textContent = `Age: ${student.age}`;

  const ageInput = document.createElement("input");
  ageInput.type = "number";
  ageInput.min = "1";
  ageInput.value = student.age;
  ageInput.className = "age-input";

  const saveBtn = document.createElement("button");
  saveBtn.type = "button";
  saveBtn.className = "save-age-btn";
  saveBtn.textContent = "Save Age";

  ageRow.append(ageLabel, ageInput, saveBtn);

  const actions = document.createElement("div");
  actions.className = "card-actions";

  const deleteBtn = document.createElement("button");
  deleteBtn.type = "button";
  deleteBtn.className = "delete-btn";
  deleteBtn.textContent = "Delete";

  actions.append(deleteBtn);

  card.append(name, email, ageRow, actions);
  return card;
}

async function loadRoster() {
  try {
    const students = await apiFetch("/students/");
    rosterCards.innerHTML = ""; 
    for (const student of students) {
      rosterCards.appendChild(createStudentCard(student));
    }
    hideError();
  } catch (err) {
    showError(err.message);
  }
}


rosterList.addEventListener("click", async (event) => {
  const card = event.target.closest(".student-card");
  if (!card) return; 

  const studentId = card.dataset.id;

  if (event.target.matches(".save-age-btn")) {
    const input = card.querySelector(".age-input");
    const newAge = Number(input.value);
    try {
      await apiFetch(`/students/${studentId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ age: newAge }),
      });
      card.querySelector(".age-display").textContent = `Age: ${newAge}`;
      hideError();
    } catch (err) {
      showError(err.message);
    }
  }

  if (event.target.matches(".delete-btn")) {
    try {
      await apiFetch(`/students/${studentId}`, { method: "DELETE" });
      card.remove();
      hideError();
    } catch (err) {
      showError(err.message);
    }
  }
});

// ---- Add-student form ----
const studentForm = document.getElementById("student-form");

studentForm.addEventListener("submit", async (event) => {
  event.preventDefault(); // stop the browser's default full-page-reload submit

  const name = document.getElementById("name-input").value.trim();
  const email = document.getElementById("email-input").value.trim();
  const age = Number(document.getElementById("age-input").value);

  try {
    const newStudent = await apiFetch("/students/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, age }),
    });
    rosterCards.appendChild(createStudentCard(newStudent));
    studentForm.reset();
    hideError();
  } catch (err) {
    showError(err.message);
  }
});

// =============================================================================
// Sort / Search / Report panel (Part 2 algorithms, called over the network)
// =============================================================================

document.getElementById("sort-btn").addEventListener("click", async () => {
  const by = document.getElementById("sort-field").value;
  const resultsList = document.getElementById("sort-results");
  try {
    const sorted = await apiFetch(`/students/sorted?by=${by}`);
    resultsList.innerHTML = "";
    for (const student of sorted) {
      const li = document.createElement("li");
      li.textContent = `${student.name} - ${by === "age" ? student.age : student.email}`;
      resultsList.appendChild(li);
    }
    hideError();
  } catch (err) {
    showError(err.message);
  }
});

document.getElementById("search-name-btn").addEventListener("click", async () => {
  const name = document.getElementById("search-name-input").value.trim();
  const resultEl = document.getElementById("search-name-result");
  try {
    const student = await apiFetch(`/students/search?name=${encodeURIComponent(name)}`);
    resultEl.textContent = `Found: ${student.name} (age ${student.age}, ${student.email})`;
    hideError();
  } catch (err) {
    resultEl.textContent = "No student found with that exact name.";
   
  }
});

document.getElementById("report-btn").addEventListener("click", async () => {
  const minAge = document.getElementById("report-min-age").value;
  const output = document.getElementById("report-output");
  try {
    const data = await apiFetch(`/students/report?min_age=${minAge}`);
    output.textContent = `${data.report}\n\nStudents meeting min age: ${data.count_meeting_min_age}`;
    hideError();
  } catch (err) {
    showError(err.message);
  }
});



document.getElementById("summarize-btn").addEventListener("click", async () => {
  const text = document.getElementById("notes-textarea").value;
  const output = document.getElementById("summary-output");
  try {
    const summary = await apiFetch("/assistant/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    output.textContent =
      `Topic: ${summary.topic}\n` +
      `Difficulty: ${summary.difficulty}\n` +
      `Key points:\n` +
      summary.key_points.map((p) => ` - ${p}`).join("\n");
    hideError();
  } catch (err) {
    showError(err.message);
  }
});

document.getElementById("notes-search-btn").addEventListener("click", async () => {
  const query = document.getElementById("notes-search-input").value;
  const resultsList = document.getElementById("notes-search-results");
  try {
    const data = await apiFetch(`/assistant/search?query=${encodeURIComponent(query)}`);
    resultsList.innerHTML = "";
    for (const note of data.results) {
      const li = document.createElement("li");
      li.textContent = `[score ${note.score.toFixed(3)}] ${note.text}`;
      resultsList.appendChild(li);
    }
    hideError();
  } catch (err) {
    showError(err.message);
  }
});


document.addEventListener("DOMContentLoaded", loadRoster);
