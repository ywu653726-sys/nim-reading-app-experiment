import json
import time
from ai_analyzer import analyze_text

TEST_CASES = [
    {
        "name": "中文短文與長難句",
        "text": (
            "隨著行動學習普及，學生常在通勤時閱讀長篇報導或課程講義，"
            "但若文章缺乏結構整理且句型層層嵌套，不僅容易分心，也會拉長理解時間。"
            "透過大語言模型自動產生精簡摘要、關鍵詞與句法拆解，能協助學習者在有限時間內掌握核心重點。"
        ),
    },
    {
        "name": "英文段落與複合子句",
        "text": (
            "Although large language models have demonstrated strong capabilities in text summarization "
            "and syntactic explanation, deploying them reliably in mobile learning applications still requires "
            "structured output validation and clear error handling when network latency fluctuates."
        ),
    },
    {
        "name": "空白輸入防呆測試",
        "text": "   ",
    },
]

if __name__ == "__main__":
    for case in TEST_CASES:
        start = time.perf_counter()
        result = analyze_text(case["text"])
        elapsed = time.perf_counter() - start
        print(f"=== {case['name']}（耗時 {elapsed:.2f} 秒）===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()