CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE interviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    role_target TEXT,
    interview_type TEXT,
    status TEXT DEFAULT 'scheduled',
    jd_text TEXT,
    resume_text TEXT,
    post_interview_report TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE interview_turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interview_id INTEGER,
    turn_number INTEGER,
    question_text TEXT,
    user_answer_text TEXT,
    retrieved_facts TEXT,
    correctness_score INTEGER,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(interview_id) REFERENCES interviews(id)
);

CREATE TABLE domain_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_category TEXT,
    topic TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
