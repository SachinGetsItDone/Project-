import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useInterviewSession } from '../context/InterviewSessionContext.jsx'
import './InterviewRoom.css'

export default function InterviewRoom() {
  const { session, clearSession } = useInterviewSession()
  const navigate = useNavigate()
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState([
    { speaker: 'ai', text: 'Welcome — whenever you\'re ready, click "Start answering" and walk me through your background.' },
  ])
  const transcriptEndRef = useRef(null)

  // Guard: you can't land here without having gone through the modal.
  useEffect(() => {
    if (!session) navigate('/')
  }, [session, navigate])

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcript])

  if (!session) return null

  function handleEndInterview() {
    clearSession()
    navigate('/')
  }

  // Placeholder — replace with the real call to the ML teammate's
  // question-generation / speech endpoint once it's ready.
  function handleToggleRecording() {
    setIsRecording((prev) => !prev)
  }

  return (
    <div className="room">
      <header className="room__nav">
        <div className="room__nav-left">
          <span className="room__dot" />
          <span>Prepline</span>
        </div>
        <div className="room__nav-meta">
          <span className="eyebrow">{session.role || 'General role'}</span>
          <span className="room__resume-chip">{session.resumeName}</span>
        </div>
        <button className="room__end" onClick={handleEndInterview}>End interview</button>
      </header>

      <div className="room__body">
        <div className="room__left">
          <div className="panel panel--user">
            <span className="eyebrow">You</span>
            <div className="panel__avatar panel__avatar--user">U</div>
            <span className={`panel__status ${isRecording ? 'panel__status--live' : ''}`}>
              {isRecording ? 'Listening…' : 'Muted'}
            </span>
          </div>

          <div className="panel panel--ai">
            <span className="eyebrow">Interviewer</span>
            <div className="panel__avatar panel__avatar--ai">AI</div>
            <span className="panel__status">Ready</span>
          </div>

          <div className="action-buttons">
            <button
              className={`btn-record ${isRecording ? 'btn-record--active' : ''}`}
              onClick={handleToggleRecording}
            >
              {isRecording ? 'Stop answering' : 'Start answering'}
            </button>
            <button className="btn-secondary">Skip question</button>
          </div>
        </div>

        <div className="panel panel--transcript">
          <div className="panel__transcript-header">
            <span className="eyebrow">Transcript</span>
          </div>
          <div className="transcript__scroll">
            {transcript.map((line, i) => (
              <p key={i} className={`transcript__line transcript__line--${line.speaker}`}>
                <span className="transcript__speaker">
                  {line.speaker === 'ai' ? 'Interviewer' : 'You'}
                </span>
                {line.text}
              </p>
            ))}
            <div ref={transcriptEndRef} />
          </div>
        </div>
      </div>
    </div>
  )
}
