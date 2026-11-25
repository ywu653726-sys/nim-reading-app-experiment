import sqlite3

conn = sqlite3.connect("experiment.db")
cur = conn.cursor()

participants = [
    ("S01", "Android", "機型A"),
    ("S02", "iOS", "機型B"),
    ("S03", "Android", "機型C"),
    ("S04", "iOS", "機型D"),
    ("S05", "Android", "機型E"),
]
cur.executemany(
    "INSERT OR IGNORE INTO participants (participant_code, platform, device_model) VALUES (?, ?, ?)",
    participants,
)

articles = [
    (
        "文章1標題",
        "中文新聞",
        "zh",
        500,
        "short",
        "貼上第1篇文章內容",
        "貼上第1篇長難句標準對照",
    ),
    (
        "文章2標題",
        "英文學術摘要",
        "en",
        1800,
        "long",
        "Paste article 2 content",
        "Paste article 2 reference",
    ),
]
cur.executemany(
    "INSERT INTO articles (title, category, language, word_count, length_group, raw_text, reference_notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
    articles,
)

quiz_questions = [
    (1, "core_concept", "第1篇核心概念題", "A"),
    (1, "hard_sentence", "第1篇長難句文意題", "B"),
    (2, "core_concept", "Article 2 core question", "C"),
    (2, "hard_sentence", "Article 2 hard sentence question", "D"),
]
cur.executemany(
    "INSERT INTO quiz_questions (article_id, question_type, question_text, correct_option) VALUES (?, ?, ?, ?)",
    quiz_questions,
)

conn.commit()
conn.close()
print("初始測試資料寫入完成！")