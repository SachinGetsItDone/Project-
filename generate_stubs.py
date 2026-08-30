import os

files = {
    "context/AuthContext.jsx": """import React from 'react';
export const AuthProvider = ({ children }) => <>{children}</>;
""",
    "components/ProtectedRoute.jsx": """import React from 'react';
export default function ProtectedRoute({ children }) {
  return <>{children}</>;
}
""",
    "styles/tokens.css": "/* Placeholder for tokens.css */\n",
    "pages/LoginPage.jsx": "export default () => <div>LoginPage</div>;",
    "pages/onboarding/PlacementQuiz.jsx": "export default () => <div>PlacementQuiz</div>;",
    "pages/onboarding/ModeSelection.jsx": "export default () => <div>ModeSelection</div>;",
    "pages/onboarding/ScoreReveal.jsx": "export default () => <div>ScoreReveal</div>;",
    "pages/onboarding/StreakDay1.jsx": "export default () => <div>StreakDay1</div>;",
    "pages/onboarding/StreakGoal.jsx": "export default () => <div>StreakGoal</div>;",
    "pages/onboarding/SessionResult.jsx": "export default () => <div>SessionResult</div>;",
    "pages/ProfileSetupPage.jsx": "export default () => <div>ProfileSetupPage</div>;",
    "pages/ProfileFirstVisit.jsx": "export default () => <div>ProfileFirstVisit</div>;",
    "pages/AvatarEditor.jsx": "export default () => <div>AvatarEditor</div>;",
    "pages/HomePage.jsx": "export default () => <div>HomePage</div>;",
    "pages/PracticePath.jsx": "export default () => <div>PracticePath</div>;",
    "pages/InterviewMatches.jsx": "export default () => <div>InterviewMatches</div>;",
    "pages/InterviewSetup.jsx": "export default () => <div>InterviewSetup</div>;",
    "pages/InterviewCall.jsx": "export default () => <div>InterviewCall</div>;",
    "pages/InterviewReport.jsx": "export default () => <div>InterviewReport</div>;",
    "pages/Quests.jsx": "export default () => <div>Quests</div>;",
    "pages/Leaderboard.jsx": "export default () => <div>Leaderboard</div>;",
    "pages/Feed.jsx": "export default () => <div>Feed</div>;",
    "pages/SettingsPage.jsx": "export default () => <div>SettingsPage</div>;",
    "pages/LoadingScreen.jsx": "export default () => <div>LoadingScreen</div>;"
}

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        # Add React import for the simple arrow function components
        if 'export default () =>' in content:
            f.write("import React from 'react';\\n" + content)
        else:
            f.write(content)

print("Stubs generated successfully!")
