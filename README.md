# Prepline — Home Page + Interview Room

React + Vite. Two pages: `/` (Home) and `/interview` (Interview Room), connected
via `InterviewSessionContext` — Home collects the resume + job description in
a modal, then hands that data to the Interview Room through context (backed by
`sessionStorage` so it survives a refresh).

## Run it

```bash
npm install
npm run dev
```

## Where your teammate's ML work plugs in

Everything AI-related is stubbed so the UI works standalone right now:

- `src/context/InterviewSessionContext.jsx` → `startSession()` is where you'll
  eventually POST the resume + JD to the backend instead of just storing it locally.
- `src/pages/InterviewRoom.jsx` → `handleToggleRecording()` and the `transcript`
  state are where the real speech/question-generation calls go.

## Suggested commit structure

Small, message-per-feature commits read a lot better on a grading rubric than
one giant commit. Suggested order:

```bash
git checkout -b feature/home-and-interview-room

git add package.json vite.config.js index.html
git commit -m "chore: scaffold Vite + React project"

git add src/index.css src/main.jsx src/App.jsx
git commit -m "chore: add global design tokens and app shell"

git add src/context/InterviewSessionContext.jsx
git commit -m "feat: add InterviewSessionContext to connect Home and Interview Room"

git add src/components/Navbar.jsx src/components/Navbar.css
git commit -m "feat: add shared navbar component"

git add src/pages/Home.jsx src/pages/Home.css
git commit -m "feat: build home page with hero and interview mode cards"

git add src/components/PreInterviewModal.jsx src/components/PreInterviewModal.css
git commit -m "feat: add resume + job description modal before starting interview"

git add src/pages/InterviewRoom.jsx src/pages/InterviewRoom.css
git commit -m "feat: build interview room with user/AI panels and transcript"

git push -u origin feature/home-and-interview-room
```

Then open a PR into `main`/`develop` rather than pushing straight to main —
gives you a clean PR description to point at for the commit-based grading too.

## Next steps (not yet built)

- Wire `startSession` to a real upload endpoint (resume parsing).
- Replace the transcript stub with the live speech-to-text / question feed.
- Auth (the modal currently has no login gate).
