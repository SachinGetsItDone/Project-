# SpeakPrep AI Interview Prototype

A focused, zero-setup prototype designed to showcase the core AI Interview & Diagnostics Architecture:

1. **RAG & Domain Knowledge**: Resume competencies cross-matched with target Job Descriptions.
2. **Interactive Live Call**:
   - **Whisper Speech-to-Text (STT)** with live waveform and real-time speech transcription.
   - **Local Voice Synthesis (TTS)** with animated interviewer speaking states.
   - **Webcam Video Preview**.
   - **1-Click STAR Demo Answers** for instant presentation testing.
3. **4-Pillar Diagnostic Report**:
   - 🟣 **Grammar**: Fluency status, identified sentence errors, and recommended corrections.
   - 🔵 **Pause & Pacing**: Words Per Minute (WPM), cadence meter, and awkward hesitation counts.
   - 🟠 **Repetition**: Filler words frequency tracker (`"um"`, `"like"`, `"basically"`).
   - 🟢 **Concept Clarity**: Domain accuracy score and JD match percentage.
   - **Question-by-Question Deep Dive**: Candidate transcript vs recommended STAR model responses.

---

## 🚀 How to Run

1. Navigate to this folder:
   ```bash
   cd ai-interview-prototype
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Launch the dev server:
   ```bash
   npm run dev
   ```
4. Open the displayed URL (e.g. `http://localhost:3000`) in your browser.
