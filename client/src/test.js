import fs from "fs";
import path from "path";

const root = process.cwd();

let passed = 0;
let failed = 0;

function test(name, condition) {
  if (condition) {
    console.log(`✅ PASS: ${name}`);
    passed++;
  } else {
    console.log(`❌ FAIL: ${name}`);
    failed++;
  }
}

function readFile(filePath) {
  return fs.readFileSync(path.join(root, filePath), "utf8");
}

console.log("\n=== Prepline Project Tests ===\n");

// --------------------------------------------------
// 1. Check required files
// --------------------------------------------------

const requiredFiles = [
  "package.json",
  "index.html",
  "src/App.jsx",
  "src/main.jsx",
  "src/pages/Home.jsx",
  "src/pages/InterviewRoom.jsx",
  "src/context/InterviewSessionContext.jsx",
];

requiredFiles.forEach((file) => {
  test(`File exists: ${file}`, fs.existsSync(path.join(root, file)));
});

// --------------------------------------------------
// 2. Check App.jsx routes
// --------------------------------------------------

const app = readFile("src/App.jsx");

test(
  "Home page is connected to / route",
  app.includes('<Route path="/" element={<Home />} />')
);

test(
  "Interview Room is connected to /interview route",
  app.includes('<Route path="/interview" element={<InterviewRoom />} />')
);

test(
  "InterviewSessionProvider is used",
  app.includes("<InterviewSessionProvider>")
);

// --------------------------------------------------
// 3. Check Home.jsx functionality
// --------------------------------------------------

const home = readFile("src/pages/Home.jsx");

test(
  "Home page contains AI interview button",
  home.includes("Take an AI interview")
);

test(
  "Home page opens the interview modal",
  home.includes("setModalOpen(true)")
);

test(
  "Home page starts an interview session",
  home.includes("startSession(data)")
);

test(
  "Home page navigates to interview room",
  home.includes("navigate('/interview')")
);

// --------------------------------------------------
// 4. Check InterviewSessionContext
// --------------------------------------------------

const context = readFile(
  "src/context/InterviewSessionContext.jsx"
);

test(
  "Interview session context has startSession",
  context.includes("startSession")
);

test(
  "Interview session context has clearSession",
  context.includes("clearSession")
);

test(
  "Session is stored in sessionStorage",
  context.includes("sessionStorage.setItem")
);

test(
  "Session is removed from sessionStorage",
  context.includes("sessionStorage.removeItem")
);

// --------------------------------------------------
// 5. Check InterviewRoom functionality
// --------------------------------------------------

const interviewRoom = readFile(
  "src/pages/InterviewRoom.jsx"
);

test(
  "Interview Room displays transcript",
  interviewRoom.includes("transcript.map")
);

test(
  "Interview Room has Start answering button",
  interviewRoom.includes("Start answering")
);

test(
  "Interview Room has Stop answering button",
  interviewRoom.includes("Stop answering")
);

test(
  "Interview Room has End interview button",
  interviewRoom.includes("End interview")
);

test(
  "Interview Room can clear the session",
  interviewRoom.includes("clearSession()")
);

test(
  "Interview Room redirects to Home after ending",
  interviewRoom.includes("navigate('/')")
);

// --------------------------------------------------
// Final result
// --------------------------------------------------

console.log("\n==============================");
console.log(`Tests passed: ${passed}`);
console.log(`Tests failed: ${failed}`);
console.log("==============================\n");

if (failed > 0) {
  process.exit(1);
} else {
  console.log("🎉 All tests passed!");
}
