import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar.jsx'
import PreInterviewModal from '../components/PreInterviewModal.jsx'
import { useInterviewSession } from '../context/InterviewSessionContext.jsx'
import './Home.css'

export default function Home() {
  const [modalOpen, setModalOpen] = useState(false)
  const navigate = useNavigate()
  const { startSession } = useInterviewSession()

  function handleModalSubmit(data) {
    startSession(data)
    setModalOpen(false)
    navigate('/interview')
  }

  return (
    <div className="home">
      <Navbar />

      <section className="hero container">
        <span className="eyebrow">AI-powered interview practice</span>
        <h1 className="hero__title">
          Walk into the real interview<br />already having done this one.
        </h1>
        <p className="hero__sub">
          Upload your resume and the job description. The interviewer asks
          questions built from both — then tells you exactly where you
          answered well, and where you didn't.
        </p>
        <div className="hero__actions">
          <button className="btn btn--primary" onClick={() => setModalOpen(true)}>
            Take an AI interview
          </button>
          <a href="#how-it-works" className="btn btn--ghost">How it works</a>
        </div>

        <div className="hero__waveform" aria-hidden="true">
          {Array.from({ length: 28 }).map((_, i) => (
            <span key={i} style={{ animationDelay: `${i * 0.06}s` }} />
          ))}
        </div>
      </section>

      <section className="modes container" id="how-it-works">
        <div className="mode-card">
          <span className="eyebrow">Solo · resume &amp; JD matched</span>
          <h3>1:1 AI interview</h3>
          <p>
            One interviewer, one seat. Questions are generated from your
            resume against the specific job description you're targeting.
          </p>
          <button className="mode-card__cta" onClick={() => setModalOpen(true)}>
            Start a session →
          </button>
        </div>

        <div className="mode-card mode-card--muted">
          <span className="eyebrow">Coming soon</span>
          <h3>AI group discussion</h3>
          <p>
            Practice holding your own in a panel-style discussion against
            multiple AI participants with distinct viewpoints.
          </p>
          <span className="mode-card__cta mode-card__cta--disabled">Notify me</span>
        </div>
      </section>

      <footer className="footer container" id="about">
        <p>Prepline — a student project. Built for practice, not perfection.</p>
      </footer>

      <PreInterviewModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={handleModalSubmit}
      />
    </div>
  )
}
