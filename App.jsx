import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";

import LoginPage from "./pages/LoginPage";
import PlacementQuiz from "./pages/onboarding/PlacementQuiz";
import ModeSelection from "./pages/onboarding/ModeSelection";
import ScoreReveal from "./pages/onboarding/ScoreReveal";
import StreakDay1 from "./pages/onboarding/StreakDay1";
import StreakGoal from "./pages/onboarding/StreakGoal";
import SessionResult from "./pages/onboarding/SessionResult";
import ProfileSetupPage from "./pages/ProfileSetupPage";
import ProfileFirstVisit from "./pages/ProfileFirstVisit";
import AvatarEditor from "./pages/AvatarEditor";

import HomePage from "./pages/HomePage";
import PracticePath from "./pages/PracticePath";
import InterviewMatches from "./pages/InterviewMatches";
import InterviewSetup from "./pages/InterviewSetup";
import InterviewCall from "./pages/InterviewCall";
import InterviewReport from "./pages/InterviewReport";
import Quests from "./pages/Quests";
import Leaderboard from "./pages/Leaderboard";
import Feed from "./pages/Feed";
import SettingsPage from "./pages/SettingsPage";
import LoadingScreen from "./pages/LoadingScreen";

import "./styles/tokens.css";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

function Protected({ children }) {
  return <ProtectedRoute>{children}</ProtectedRoute>;
}

export default function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* --- Auth --- */}
            <Route path="/" element={<LoginPage />} />

            {/* --- Onboarding (first-time signup flow) --- */}
            <Route path="/onboarding/quiz" element={<PlacementQuiz />} />
            <Route path="/onboarding/mode" element={<ModeSelection />} />
            <Route path="/onboarding/score" element={<ScoreReveal />} />
            <Route path="/onboarding/streak" element={<StreakDay1 />} />
            <Route path="/onboarding/streak-goal" element={<StreakGoal />} />
            <Route path="/onboarding/result" element={<SessionResult />} />
            <Route path="/onboarding/profile" element={<ProfileSetupPage />} />
            <Route path="/profile/first-visit" element={<Protected><ProfileFirstVisit /></Protected>} />
            <Route path="/profile/avatar" element={<Protected><AvatarEditor /></Protected>} />

            {/* --- Core app (protected) --- */}
            <Route path="/home" element={<Protected><HomePage /></Protected>} />
            <Route path="/practice-path" element={<Protected><PracticePath /></Protected>} />
            <Route path="/interview/matches" element={<Protected><InterviewMatches /></Protected>} />
            <Route path="/interview/setup" element={<Protected><InterviewSetup /></Protected>} />
            <Route path="/interview/call" element={<Protected><InterviewCall /></Protected>} />
            <Route path="/interview/report" element={<Protected><InterviewReport /></Protected>} />
            <Route path="/interview/report/:sessionId" element={<Protected><InterviewReport /></Protected>} />
            <Route path="/quests" element={<Protected><Quests /></Protected>} />
            <Route path="/leaderboard" element={<Protected><Leaderboard /></Protected>} />
            <Route path="/feed" element={<Protected><Feed /></Protected>} />
            <Route path="/settings" element={<Protected><SettingsPage /></Protected>} />
            <Route path="/loading" element={<Protected><LoadingScreen /></Protected>} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}
