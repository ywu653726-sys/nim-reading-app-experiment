import sqlite3

conn = sqlite3.connect("experiment.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS articles (
    article_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    language TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    length_group TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    reference_notes TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS participants (
    participant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_code TEXT UNIQUE NOT NULL,
    platform TEXT NOT NULL,
    device_model TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS test_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    is_chunked BOOLEAN NOT NULL,
    retry_count INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    response_time_sec REAL,
    llm_output_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS quality_ratings (
    rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    rater_role TEXT NOT NULL DEFAULT 'participant',
    summary_score INTEGER CHECK (summary_score BETWEEN 1 AND 5),
    keywords_score INTEGER CHECK (keywords_score BETWEEN 1 AND 5),
    hard_sentence_score INTEGER CHECK (hard_sentence_score BETWEEN 1 AND 5),
    comment TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS quiz_questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    question_type TEXT NOT NULL,
    question_text TEXT NOT NULL,
    correct_option TEXT NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS quiz_responses (
    response_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    selected_option TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL
)
""")

conn.commit()
conn.close()
print("成功建立 experiment.db！")