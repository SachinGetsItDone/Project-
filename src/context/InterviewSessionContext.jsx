import { createContext, useContext, useState, useCallback } from 'react'

/**
 * Holds the data collected on the Home page (resume + job description)
 * so the Interview Room can read it once the user starts a session.
 *
 * This is intentionally simple (React state + sessionStorage backup) so it
 * has no backend dependency yet. Swap `startSession` / `clearSession` for
 * real API calls once the ML teammate's endpoint is ready — the rest of
 * the app only depends on this context, not on how the data got here.
 */

const InterviewSessionContext = createContext(null)

const STORAGE_KEY = 'prepline_session'

export function InterviewSessionProvider({ children }) {
  const [session, setSession] = useState(() => {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  })

  const startSession = useCallback(({ resumeFile, resumeText, jobDescription, role }) => {
    const next = {
      resumeName: resumeFile?.name ?? null,
      resumeText: resumeText ?? '',
      jobDescription,
      role,
      startedAt: new Date().toISOString(),
    }
    setSession(next)
    // Files can't be JSON-serialized meaningfully; only metadata is persisted.
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    return next
  }, [])

  const clearSession = useCallback(() => {
    setSession(null)
    sessionStorage.removeItem(STORAGE_KEY)
  }, [])

  return (
    <InterviewSessionContext.Provider value={{ session, startSession, clearSession }}>
      {children}
    </InterviewSessionContext.Provider>
  )
}

export function useInterviewSession() {
  const ctx = useContext(InterviewSessionContext)
  if (!ctx) throw new Error('useInterviewSession must be used inside InterviewSessionProvider')
  return ctx
}
