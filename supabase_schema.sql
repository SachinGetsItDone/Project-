-- Enable the pgvector extension to work with embeddings for RAG
create extension if not exists vector;

-- 1. Profiles/Users Table
-- Extends Supabase auth.users to store additional user info
create table public.profiles (
  id uuid references auth.users on delete cascade not null primary key,
  first_name text,
  last_name text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. Interviews Table
-- Stores the high-level session for a single interview
create table public.interviews (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  role_target text not null, -- e.g., 'Software Engineer', 'Product Manager'
  interview_type text not null, -- e.g., 'Technical', 'HR', 'Behavioral'
  status text check (status in ('scheduled', 'in_progress', 'completed', 'failed')) default 'scheduled',
  jd_text text, -- Job description context
  resume_text text, -- User's resume context
  post_interview_report jsonb, -- Final report (scores, summary, improvement areas)
  started_at timestamp with time zone,
  completed_at timestamp with time zone,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. Interview Turns (Transcript) Table
-- Stores each back-and-forth interaction within an interview
create table public.interview_turns (
  id uuid default gen_random_uuid() primary key,
  interview_id uuid references public.interviews(id) on delete cascade not null,
  turn_number integer not null,
  question_text text not null, -- What the AI interviewer asked
  user_answer_text text, -- What the user replied (from STT)
  retrieved_facts jsonb, -- Facts pulled from RAG used to evaluate the answer
  correctness_score integer, -- 0-10 or 0-100 score given by the LLM
  feedback text, -- Specific feedback for this answer
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  
  unique(interview_id, turn_number)
);

-- 4. Domain Knowledge (RAG) Table
-- Stores facts, definitions, and standard answers for the vector search
create table public.domain_knowledge (
  id uuid default gen_random_uuid() primary key,
  role_category text not null, -- e.g., 'Software Engineering', 'Marketing'
  topic text not null, -- e.g., 'System Design', 'React', 'Agile'
  content text not null, -- The actual fact or best-practice documentation
  embedding vector(1536), -- Vector representation (OpenAI uses 1536 dimensions)
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Index for vector similarity search on domain knowledge
create index on public.domain_knowledge using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

-- Enable Row Level Security (RLS)
alter table public.profiles enable row level security;
alter table public.interviews enable row level security;
alter table public.interview_turns enable row level security;
alter table public.domain_knowledge enable row level security;

-- RLS Policies

-- Profiles: Users can read and update their own profile
create policy "Users can view own profile" 
on profiles for select using (auth.uid() = id);

create policy "Users can update own profile" 
on profiles for update using (auth.uid() = id);

-- Interviews: Users can read and create their own interviews
create policy "Users can view own interviews" 
on interviews for select using (auth.uid() = user_id);

create policy "Users can create own interviews" 
on interviews for insert with check (auth.uid() = user_id);

create policy "Users can update own interviews" 
on interviews for update using (auth.uid() = user_id);

-- Interview Turns: Users can read and create turns for their own interviews
create policy "Users can view turns of own interviews" 
on interview_turns for select using (
  exists (select 1 from interviews where interviews.id = interview_turns.interview_id and interviews.user_id = auth.uid())
);

create policy "Users can create turns for own interviews" 
on interview_turns for insert with check (
  exists (select 1 from interviews where interviews.id = interview_turns.interview_id and interviews.user_id = auth.uid())
);

-- Domain Knowledge: Everyone (authenticated) can read, only admins (or service role) can write
create policy "Anyone can read domain knowledge" 
on domain_knowledge for select to authenticated using (true);

-- Note: In production, consider creating a function/trigger to update 'updated_at' timestamps
