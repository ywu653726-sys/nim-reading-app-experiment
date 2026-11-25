import csv
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "experiment.db"


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("=== 1. 端對端回應時間統計（短文 <=5s、長文 <=15s）===")
    rows = cur.execute("""
        SELECT
            a.length_group,
            p.platform,
            COUNT(*) AS total_runs,
            SUM(CASE WHEN r.status = 'success' THEN 1 ELSE 0 END) AS success_runs,
            ROUND(AVG(CASE WHEN r.status = 'success' THEN r.response_time_sec END), 3) AS avg_sec,
            ROUND(
                100.0 * SUM(
                    CASE
                        WHEN r.status = 'success' AND a.length_group = 'short' AND r.response_time_sec <= 5.0 THEN 1
                        WHEN r.status = 'success' AND a.length_group = 'long' AND r.response_time_sec <= 15.0 THEN 1
                        ELSE 0
                    END
                ) / NULLIF(SUM(CASE WHEN r.status = 'success' THEN 1 ELSE 0 END), 0),
                1
            ) AS pass_rate_pct
        FROM test_runs r
        JOIN articles a ON r.article_id = a.article_id
        JOIN participants p ON r.participant_id = p.participant_id
        GROUP BY a.length_group, p.platform
    """).fetchall()
    for row in rows:
        print(row)

    print("\n=== 2. 人工品質評分（李克特 1~5 分平均）===")
    ratings = cur.execute("""
        SELECT
            rater_role,
            COUNT(*) AS n,
            ROUND(AVG(summary_score), 2) AS avg_summary,
            ROUND(AVG(keywords_score), 2) AS avg_keywords,
            ROUND(AVG(hard_sentence_score), 2) AS avg_hard_sentence
        FROM quality_ratings
        GROUP BY rater_role
    """).fetchall()
    for row in ratings:
        print(row)

    print("\n=== 3. 閱讀理解測驗答對率 ===")
    quiz = cur.execute("""
        SELECT
            q.question_type,
            COUNT(*) AS total_q,
            SUM(CASE WHEN qr.is_correct = 1 THEN 1 ELSE 0 END) AS correct_q,
            ROUND(100.0 * SUM(CASE WHEN qr.is_correct = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS accuracy_pct
        FROM quiz_responses qr
        JOIN quiz_questions q ON qr.question_id = q.question_id
        GROUP BY q.question_type
    """).fetchall()
    for row in quiz:
        print(row)

    # 匯出明細 CSV 方便開 Excel 做圖或進階統計
    export_rows = cur.execute("""
        SELECT
            r.run_id,
            p.participant_code,
            p.platform,
            a.article_id,
            a.title,
            a.language,
            a.length_group,
            r.is_chunked,
            r.retry_count,
            r.status,
            r.response_time_sec,
            qr_rate.summary_score,
            qr_rate.keywords_score,
            qr_rate.hard_sentence_score
        FROM test_runs r
        JOIN participants p ON r.participant_id = p.participant_id
        JOIN articles a ON r.article_id = a.article_id
        LEFT JOIN quality_ratings qr_rate ON r.run_id = qr_rate.run_id AND qr_rate.rater_role = 'participant'
        ORDER BY r.run_id
    """).fetchall()

    csv_path = Path(__file__).resolve().parent / "experiment_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "run_id", "participant_code", "platform", "article_id", "title",
            "language", "length_group", "is_chunked", "retry_count", "status",
            "response_time_sec", "summary_score", "keywords_score", "hard_sentence_score"
        ])
        writer.writerows(export_rows)

    conn.close()
    print(f"\n已匯出明細至：{csv_path}")


if __name__ == "__main__":
    main()