import json
import os
from typing import Any
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL_NAME = "mistralai/mistral-large-4-1t-a52b"
BASE_URL = "https://integrate.api.nvidia.com/v1"

SYSTEM_PROMPT = """你是一位專業的閱讀理解與句法分析助手。
請針對使用者提供的文章內容，嚴格以「純 JSON 格式」輸出，不要加上 markdown 程式碼區塊（不要 ```json），也不要輸出多餘的開頭或結尾說明。

請嚴格遵守以下 JSON 結構：
{
  "status": "success",
  "summary": "語意連貫、精簡的核心重點摘要（非單純擷取原句）",
  "keywords": ["關鍵詞1", "關鍵詞2"],
  "complex_sentences": [
    {
      "original": "文章中結構最複雜的原句（挑出 2～3 句）",
      "structure": "主句／子句／修飾語結構拆解",
      "plain_explanation": "白話說明"
    }
  ],
  "error_message": null
}

規則：
1. keywords 請萃取出 5～8 個主題關鍵詞。
2. complex_sentences 請挑出 2～3 句結構最複雜的句子；若文章較短不足 2 句，則挑出最複雜的句子並清楚拆解。
3. 若無法順利分析，請將 status 設為 "error"，並在 error_message 填入簡短錯誤原因。
"""


def _error_response(message: str) -> dict[str, Any]:
    return {
        "status": "error",
        "summary": "",
        "keywords": [],
        "complex_sentences": [],
        "error_message": message,
    }


def _normalize_result(data: Any, raw_content: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        return _error_response(f"回傳格式非 JSON 物件｜原始輸出：{raw_content[:300]}")

    status = data.get("status", "success")
    if status != "success":
        return _error_response(data.get("error_message") or "模型回傳非成功狀態")

    summary = data.get("summary")
    keywords = data.get("keywords")
    complex_sentences = data.get("complex_sentences")

    if not isinstance(summary, str):
        summary = ""
    if not isinstance(keywords, list):
        keywords = []
    if not isinstance(complex_sentences, list):
        complex_sentences = []

    normalized_sentences = []
    for item in complex_sentences:
        if isinstance(item, dict):
            normalized_sentences.append(
                {
                    "original": str(item.get("original", "")),
                    "structure": str(item.get("structure", "")),
                    "plain_explanation": str(item.get("plain_explanation", "")),
                }
            )

    return {
        "status": "success",
        "summary": summary.strip(),
        "keywords": [str(k).strip() for k in keywords if str(k).strip()],
        "complex_sentences": normalized_sentences,
        "error_message": None,
    }


def analyze_text(text: str) -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        return _error_response("輸入內容為空，請提供有效文字。")

    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        return _error_response("尚未設定 NVIDIA_API_KEY 環境變數。")

    client = OpenAI(
    base_url=BASE_URL,
    api_key=api_key,
    timeout=40.0,
    max_retries=1,
)

    last_error = ""
    for _ in range(1):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                temperature=0.25,
                max_tokens=4096,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"請分析以下內容：\n\n{text.strip()}"},
                ],
            )
            raw_content = (response.choices[0].message.content or "").strip()
        except Exception as e:
            return _error_response(f"NVIDIA NIM API 呼叫失敗：{e}")

        if raw_content.startswith("```"):
            lines = raw_content.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw_content = "\n".join(lines).strip()

        try:
            parsed = json.loads(raw_content)
            return _normalize_result(parsed, raw_content)
        except json.JSONDecodeError as e:
            last_error = f"JSON 解析失敗：{e}｜原始輸出：{raw_content[:300]}"

    return _error_response(last_error)