import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { InterviewSessionProvider } from './context/InterviewSessionContext.jsx'
import Home from './pages/Home.jsx'
import InterviewRoom from './pages/InterviewRoom.jsx'

export default function App() {
  return (
    <InterviewSessionProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/interview" element={<InterviewRoom />} />
        </Routes>
      </BrowserRouter>
    </InterviewSessionProvider>
  )
}
