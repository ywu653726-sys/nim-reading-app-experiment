import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "experiment.db"


def get_or_create_participant_id(conn: sqlite3.Connection, participant_code: str, platform: str = "Android") -> int:
    cur = conn.cursor()
    row = cur.execute(
        "SELECT participant_id FROM participants WHERE participant_code = ?",
        (participant_code,)
    ).fetchone()
    if row:
        return row[0]

    cur.execute(
        "INSERT INTO participants (participant_code, platform) VALUES (?, ?)",
        (participant_code, platform)
    )
    conn.commit()
    return cur.lastrowid


def log_test_run(
    article_id: int,
    participant_code: str,
    is_chunked: bool,
    retry_count: int,
    status: str,
    response_time_sec: float,
    llm_output: dict | str | None,
    platform: str = "Android",
) -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        participant_id = get_or_create_participant_id(conn, participant_code, platform)

        if llm_output is None:
            output_str = None
        elif isinstance(llm_output, str):
            output_str = llm_output
        else:
            output_str = json.dumps(llm_output, ensure_ascii=False)

        cur.execute(
            """
            INSERT INTO test_runs (
                article_id,
                participant_id,
                is_chunked,
                retry_count,
                status,
                response_time_sec,
                llm_output_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                article_id,
                participant_id,
                1 if is_chunked else 0,
                retry_count,
                status,
                round(response_time_sec, 3),
                output_str,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()