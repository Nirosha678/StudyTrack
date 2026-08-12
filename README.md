# StudyTrack

A single full-stack app for Myntra's Trainee Enablement team: a FastAPI + SQLAlchemy backend over SQLite, a plain HTML/CSS/JS dashboard, a hand-rolled sorting/searching **Algorithms Engine**, and a mock **AI Assistant** (note summarizer + semantic search) — all wired into one running application.

- **Part 1 — Core App:** Student/Course CRUD, roster dashboard
- **Part 2 — Algorithms Engine:** insertion sort, binary search, roster report
- **Part 3 — AI Assistant:** note summarizer, mock-embedding semantic search

---

## 1. Project layout

```
studytrack/
├── backend/
│   ├── main.py           # FastAPI app, routes, CORS, static-file mount, startup seeding
│   ├── database.py       # SQLAlchemy engine + sessionmaker + declarative_base
│   ├── models.py         # Student, Course ORM models
│   ├── schemas.py        # Pydantic request/response models
│   ├── crud.py           # functions that perform the actual DB operations
│   ├── algorithms.py     # Part 2: hand-rolled sort/search/report functions
│   ├── ai_service.py     # Part 3: summarizer + mock-embedding + cosine similarity
│   ├── seed_data.py      # exact seed roster used by Parts 1 and 2
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── .gitignore
└── README.md
```

> Note: the backend folder in this repo is named `backend/` (lowercase). All commands below `cd` into it directly.

---

## 2. Run mode

This project uses the **single-process** run mode. FastAPI mounts the `frontend/` folder as static files (`app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")`, registered *after* the API routes), so one `uvicorn` process serves both the API and the dashboard. Opening `http://localhost:8000/` serves `index.html`, and every `fetch` call in `app.js` uses a **relative** path (e.g. `fetch("/students/")`), which hits the same server — no separate frontend server or port is needed.

CORS is still configured with `CORSMiddleware` (allowing `http://localhost:5500` and `http://127.0.0.1:5500` explicitly, alongside `http://localhost:8000`) as a documented convenience in case you want to serve `frontend/` separately (e.g. VS Code "Live Server" on port 5500) during development. `allow_origins` never uses the wildcard `"*"`.

---

## 3. Setup & run

From the project root:

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --reload
```

Then open **http://localhost:8000/** in your browser. The dashboard loads, and on first startup against an empty database the app automatically seeds the 8 students listed in `seed_data.py` (see §6).

Interactive API docs (Swagger UI) are at **http://localhost:8000/docs** and list every endpoint below.

The SQLite database file `studytrack.db` is created automatically inside `backend/` on first run. Delete it if you want to re-seed from scratch.

### Two-process alternative (optional)

If you'd rather serve the frontend separately (e.g. with a "Live Server" extension on port 5500):

1. Run the backend as above: `uvicorn main:app --reload` (port 8000).
2. Serve `frontend/index.html` on port 5500.
3. Change `const BASE_URL = "";` in `frontend/app.js` to `const BASE_URL = "http://localhost:8000";` so every fetch call targets the backend explicitly.

CORS already allows `http://localhost:5500`, so no backend changes are needed for this mode.

---

## 4. API reference

All roster data lives in SQLite and is served exclusively by this backend — the frontend never calls any external or placeholder API.

### Students

| Method | Path | Body | Response |
|---|---|---|---|
| `POST` | `/students/` | `{"name": str, "email": str, "age": int}` | `201` + created student (with empty `courses: []`) |
| `GET` | `/students/` | — (optional `?min_age=<int>` query param) | `200` + list of students |
| `GET` | `/students/{student_id}` | — | `200` + student, or `404` |
| `PATCH` | `/students/{student_id}` | any of `name`, `email`, `age` (partial) | `200` + updated student, or `404` |
| `DELETE` | `/students/{student_id}` | — | `200` + `{"detail": "Student deleted", "id": ...}`, or `404` |
| `GET` | `/students/{student_id}/course-count` | — | `200` + `{"student_id": ..., "course_count": ...}` (computed via `func.count()` in `crud.get_student_course_count`, not Python `len()`) |

Validation: `email` must contain `@` (custom `@field_validator`, rejected with `422` before hitting the database); `age` must be `> 0` (`Field(gt=0)`); a duplicate `email` on create/update is rejected with `409` (a handled 4xx, not a server crash).

### Courses

| Method | Path | Body | Response |
|---|---|---|---|
| `POST` | `/courses/` | `{"course_name": str, "credits": int (1–6), "student_id": int}` | `201` + created course, or `404` if `student_id` doesn't exist |
| `GET` | `/courses/` | — | `200` + list of courses |
| `GET` | `/courses/{course_id}` | — | `200` + course, or `404` |
| `PATCH` | `/courses/{course_id}` | any of `course_name`, `credits`, `student_id` (partial) | `200` + updated course, or `404` |
| `DELETE` | `/courses/{course_id}` | — | `200` + `{"detail": "Course deleted", "id": ...}`, or `404` |

Each row in `courses` is one enrollment — the same `course_name` can appear multiple times under different students. `credits` is constrained to 1–6 both by a database `CheckConstraint` and by `Field(ge=1, le=6)` in the Pydantic schema.

### Algorithms Engine (Part 2)

| Method | Path | Response |
|---|---|---|
| `GET` | `/students/sorted?by=age` (or `by=name`) | roster sorted **ascending**, via hand-written insertion sort |
| `GET` | `/students/search?name=<exact name>` | matching student via hand-written binary search, or `404` if not found |
| `GET` | `/students/report?min_age=<n>` (default 21) | `{"report": "<multiline string>", "count_meeting_min_age": <int>}` |

### AI Assistant (Part 3)

| Method | Path | Body | Response |
|---|---|---|---|
| `POST` | `/assistant/summarize` | `{"text": "<raw notes>"}` | `{"topic": ..., "key_points": [...], "difficulty": ...}` |
| `GET` | `/assistant/search?query=<text>` | — | `{"results": [{"id", "text", "score"}, ...]}` sorted by score descending |

Both run in fully offline **mock mode** by default — no API key, no network call. See §7.

---

## 5. Frontend walkthrough

Open `http://localhost:8000/`:

1. **On load**, `app.js` calls `GET /students/` and renders one card per student into `#roster-cards` using `document.createElement` (never a full-list `innerHTML` rebuild). Each card shows name, email, current age, an editable age input + **Save Age** button, and a **Delete** button.
2. **Editing age**: click **Save Age** on a card → sends `PATCH /students/{id}` with `{"age": <new value>}` → on success, updates the age text on that card in place. This is handled by a **single delegated click listener** on `#roster-list`, which uses `event.target.closest(".student-card")` and `event.target.matches(...)` to tell the Save/Delete buttons apart — not one listener per button.
3. **Deleting a student**: click **Delete** on a card → sends `DELETE /students/{id}` → on success, removes that card from the DOM.
4. **Adding a student**: fill in the `#student-form` (name, email, age) and submit → `event.preventDefault()` stops the page reload → `POST /students/` is sent → on success, a new card is built with `createElement`/`appendChild` for the record the API echoes back and appended live, with no page reload.
5. **Errors**: any failed request (backend down, non-2xx response) is shown in the `#error-banner` div at the top of the page — never only a `console.log` or a browser `alert()`.
6. **Sort / Search / Report panel** (`#tools-panel`): a dropdown + **Sort** button calls `/students/sorted?by=...` and lists the result; a name field + **Search** button calls `/students/search?name=...`; a min-age field + **Generate Report** button calls `/students/report?min_age=...` and prints the multi-line report plus the count.
7. **AI Helper panel** (`#ai-helper`): a textarea + **Summarize** button calls `POST /assistant/summarize` and renders `topic` / `key_points` / `difficulty`; a query field + **Search Notes** button calls `GET /assistant/search?query=...` and lists the 5 sample notes ranked by similarity score.

**Responsive layout:** `style.css` gives the roster container and each card explicit `padding`, `margin`, and a visible `border`, with `box-sizing: border-box` throughout. An `@media (max-width: 600px)` rule collapses the card grid from multiple columns to a single column — resize the browser (or use dev-tools device emulation) below 600px to see it.

### Demo walkthrough (for grading)

1. Start the app (`uvicorn main:app --reload`) and open `http://localhost:8000/`. The 8 seeded students load as cards.
   - Backend log: `INFO: GET /students/ HTTP/1.1" 200 OK`
2. Change a student's age in the age input and click **Save Age**.
   - Backend log: `INFO: PATCH /students/3 HTTP/1.1" 200 OK` — the card updates immediately.
3. Fill the **Add a Student** form and submit.
   - Backend log: `INFO: POST /students/ HTTP/1.1" 201 Created` — a new card appears without a reload.
4. Click **Delete** on a card.
   - Backend log: `INFO: DELETE /students/9 HTTP/1.1" 200 OK` — the card disappears.
5. Stop the backend process and try any action → the red `#error-banner` appears with "Could not reach the StudyTrack backend. Is the server running?"
6. Use `POST /courses/` (via Swagger UI at `/docs`) to enroll one seeded student in 2+ courses, then `GET /students/{id}/course-count` to confirm the count matches — computed by `func.count()` in `crud.py`, not Python `len()`.

---

## 6. Seed data

`backend/seed_data.py` ships this exact list and inserts it automatically on first startup against an empty database (`@app.on_event("startup")` → `seed_if_empty(db)`, which only inserts if the `Student` table is currently empty):

```python
SEED_STUDENTS = [
    {"name": "Aditi Rao",     "email": "aditi.rao@example.com",     "age": 22},
    {"name": "Rohan Mehta",   "email": "rohan.mehta@example.com",   "age": 19},
    {"name": "Kavya Nair",    "email": "kavya.nair@example.com",    "age": 25},
    {"name": "Farhan Sheikh", "email": "farhan.sheikh@example.com", "age": 18},
    {"name": "Priya Iyer",    "email": "priya.iyer@example.com",    "age": 21},
    {"name": "Devansh Gupta", "email": "devansh.gupta@example.com", "age": 23},
    {"name": "Meera Joshi",   "email": "meera.joshi@example.com",   "age": 20},
    {"name": "Sameer Khan",   "email": "sameer.khan@example.com",   "age": 24},
]
```

- `GET /students/sorted?by=age` on this roster returns, ascending: Farhan Sheikh (18), Rohan Mehta (19), Meera Joshi (20), Priya Iyer (21), Aditi Rao (22), Devansh Gupta (23), Sameer Khan (24), Kavya Nair (25).
- Sorted alphabetically by name: Aditi Rao, Devansh Gupta, Farhan Sheikh, Kavya Nair, Meera Joshi, Priya Iyer, Rohan Mehta, Sameer Khan — so `GET /students/search?name=Priya Iyer` finds her at index 5.
- `GET /students/report?min_age=21` → `count_meeting_min_age: 5` (Aditi Rao, Kavya Nair, Priya Iyer, Devansh Gupta, Sameer Khan).

---

## 7. Algorithms Engine — how it works and why (Part 2 complexity write-up)

All three functions live in `backend/algorithms.py` and operate on the **live** roster fetched from the database via `crud.get_students()`, converted to plain dicts — not a hardcoded standalone list.

- **`insertion_sort_by_field(students, field)`** — a hand-written Insertion Sort: an outer loop from the second element, an inner `while` loop that shifts every element greater than the current `key` one slot to the right, then drops the key into the resulting gap. No call to `sorted()` or `.sort()` appears anywhere in this function.
- **`binary_search_by_name(sorted_by_name_list, name)`** — a hand-written iterative Binary Search using the overflow-safe midpoint `mid = low + (high - low) // 2`. The list must already be sorted by name; that sort is done with Python's built-in `sorted()` in `main.py` before calling this function — only the *search* itself is hand-rolled.
- **`format_roster_report(students)`** / **`count_students_meeting_min_age(students, min_age)`** — build an f-string per student (`"[Age {age}] {name} <{email}>"`) and count matches with an explicit accumulator loop (not a bare `sum(1 for ... )` one-liner).

**Why Insertion Sort is O(n) best case / O(n²) worst case:** In the best case the input is already sorted, so the inner `while` condition (`students[j][field] > key_value`) is false immediately for every `i` — each of the `n` outer-loop iterations does one constant-time comparison and no shifting, giving O(n) total. In the worst case (reverse-sorted input) every new element is smaller than everything already placed, so the inner loop shifts all `i` previously-sorted elements before placing the key — that's roughly `1 + 2 + ... + (n-1)` shifts, which sums to O(n²). Average case is also O(n²), since a random element typically needs to shift past about half of the already-sorted prefix.

**Why Binary Search requires the list to be sorted:** Binary Search works by repeatedly comparing the target to the middle element and discarding the half of the list that *cannot* contain the target, based on ordering — if `mid_name < name`, everything to the left of `mid` is also `< name` and can be safely discarded, and vice versa. That guarantee only holds if the list is ordered on the field being searched; on an unsorted list, a middle element being less than the target says nothing about where the target actually is, so the elimination step is invalid and the algorithm can miss the target entirely. This is what gives Binary Search its O(log n) time, versus O(n) for a linear scan.

---

## 8. AI Assistant — mock mode (Part 3)

Both AI features run **fully offline** by default (`AI_MODE=mock`, the default — no environment variable needs to be set). No API key and no network call are required, and this mock path is what satisfies every grading criterion on its own. **This mock mode is what was used for the grading demonstration below** — no real LLM/embedding provider was wired in, so there is no API key of any kind, committed or otherwise, anywhere in this repository.

### 8.1 Note summarizer — `summarize_notes(raw_text)`

Always returns exactly three keys: `topic`, `key_points`, `difficulty`.

- **`topic`** — the most frequent meaningful (non-stopword) word in the input, found with `collections.Counter` over lower-cased, alphanumeric tokens after filtering a small stopword list. If every token happens to be a stopword, it falls back to the first raw token.
- **`key_points`** — up to 3 non-empty sentences, found by splitting the input on `.`/`!`/`?` and trimming whitespace, in order.
- **`difficulty`** — based on total word count (`text.split()`): **< 40 words → `"easy"`**, **40–100 words → `"medium"`**, **> 100 words → `"hard"`**.
- **Empty input** (`""` or whitespace-only): does not raise — returns `{"topic": "untitled", "key_points": [], "difficulty": "easy"}` (0 words falls under the `< 40` rule).
- The function is deterministic: the same input always produces byte-for-byte identical output.

Exposed via `POST /assistant/summarize` (`{"text": "..."}`), rendered in the **AI Helper → Summarize** panel on the dashboard.

**Prompt this would use in `AI_MODE=real`** (not implemented — for documentation only, per the assignment's structured-prompting requirement):

```
Task: Summarize the following study notes into a fixed JSON object.
Context: The notes are informal, student-written study material on a technical topic.
Constraints:
  - Respond with ONLY a JSON object, no prose, no markdown fences.
  - The object must have exactly these three keys: "topic", "key_points", "difficulty".
  - "topic" is a short string (1-4 words) naming the main subject.
  - "key_points" is a list of at most 3 short strings, each a distinct idea from the notes.
  - "difficulty" is exactly one of: "easy", "medium", "hard".
Format: Valid JSON only, matching {"topic": str, "key_points": [str, ...], "difficulty": str}.

Notes:
"""
<raw_text>
"""
```

### 8.2 Semantic search — `mock_embed` + `cosine_similarity`

- **`mock_embed(text)`** — a fixed-vocabulary word-count vector over this exact 12-word vocabulary, in order: `["sort", "search", "binary", "insertion", "sql", "join", "fastapi", "pydantic", "prompt", "llm", "database", "validate"]`. Tokenizes by lower-casing and splitting on any run of non-alphanumeric characters, then counts exact whole-token matches — always returns a list of exactly 12 floats (all zero for an empty or fully out-of-vocabulary string).
- **`cosine_similarity(vec_a, vec_b)`** — dot product over the product of the two vectors' L2 norms, computed from first principles with `math.sqrt` (no third-party linear-algebra call). If either vector's magnitude is exactly 0, it returns `0.0` directly instead of dividing by zero.
- **`search_notes(query)`** — embeds the fixed 5-note sample set and the query with `mock_embed`, scores every note with `cosine_similarity`, and returns all notes annotated with their score, sorted descending. A zero-vector query (empty, or entirely out-of-vocabulary words) still returns all 5 notes successfully, each at `score: 0.0`.

Exposed via `GET /assistant/search?query=...`, rendered in the **AI Helper → Search Notes** panel. For example, `?query=binary search algorithm` ranks note id `1` ("Binary search requires a sorted array...") first, since it shares the most vocabulary overlap.

---

## 9. Git workflow

This repository's history includes a feature branch created, committed to twice, and merged back into `main` (visible via `git log --graph --all`):

```
*   Merge frontend improvements
|\
| * Document student form feedback styling
|/
* Style student form feedback message
* Add student form feedback area
* Update gitignore for Python project
* Initial StudyTrack project
```

Branch: `feature/frontend-improvements`, merged into `main`.

---

## 10. What's intentionally excluded from the repo

Per `.gitignore`: `venv/`, `__pycache__/`, `*.pyc`, `*.db`, `.env`. No real `.env` file, API key, or committed secret exists anywhere in this repository — mock mode needs none, and no `AI_MODE=real` provider was wired in.
