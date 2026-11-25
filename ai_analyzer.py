import json
import os
from typing import Any
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL_NAME = "nvidia/nemotron-3.5-lightning-30b-a3b"
BASE_URL = "https://integrate.api.nvidia.com/v1"

SYSTEM_PROMPT = """你是一位專業的閱讀理解與句法分析助手。
請針對使用者提供的文章內容，嚴格以「純 JSON 格式」輸出，不要加上 markdown 程式碼區塊（不要 ```json），也不要輸出多餘的開頭或結語。

語言與數量硬性規定：
1. 除 complex_sentences 裡的 "original" 必須保留原文句字（中英文皆可）外，其餘所有文字欄位（"summary"、"keywords" 陣列元素、"structure"、"plain_explanation"）一律使用「繁體中文」，禁止使用簡體字。
2. "keywords" 請提供 5 到 8 個精準代表文章核心主題的詞彙。
3. "complex_sentences" 請挑出 2 到 3 句結構最複雜的原句，並完整填寫 "original"、"structure" 與 "plain_explanation"。

請嚴格遵守以下 JSON 結構：
{
  "status": "success",
  "summary": "語意連貫、精簡的核心重點摘要（繁體中文，非單純擷取原句）",
  "keywords": ["關鍵詞1", "關鍵詞2", "關鍵詞3", "關鍵詞4", "關鍵詞5"],
  "complex_sentences": [
    {
      "original": "文章中結構最複雜的原句（2～3 句）",
      "structure": "主句/子句/修飾語結構拆解（繁體中文）",
      "plain_explanation": "白話說明（繁體中文）"
    }
  ]
}
"""


def _error_response(message: str) -> dict[str, Any]:
    return {
        "status": "error",
        "summary": "",
        "keywords": [],
        "complex_sentences": [],
        "error_message": message,
    }


def _normalize_result(parsed: dict[str, Any], raw_text: str) -> dict[str, Any]:
    summary = parsed.get("summary")
    if not isinstance(summary, str):
        summary = str(summary or "").strip()

    keywords = parsed.get("keywords")
    if not isinstance(keywords, list):
        keywords = []
    keywords = [str(k).strip() for k in keywords if str(k).strip()]

    complex_sentences = parsed.get("complex_sentences")
    if not isinstance(complex_sentences, list):
        complex_sentences = []

    normalized_sentences: list[dict[str, str]] = []
    for item in complex_sentences:
        if isinstance(item, dict):
            orig = str(item.get("original", "")).strip()
            struct = str(item.get("structure", "")).strip()
            plain = str(item.get("plain_explanation", "")).strip()
            if orig or struct or plain:
                normalized_sentences.append(
                    {
                        "original": orig,
                        "structure": struct,
                        "plain_explanation": plain,
                    }
                )

    return {
        "status": "success",
        "summary": summary.strip(),
        "keywords": keywords,
        "complex_sentences": normalized_sentences,
        "error_message": "",
        "raw_output": raw_text,
    }


def _parse_json_object(raw_content: str) -> dict[str, Any] | None:
    text = raw_content.strip()
    if not text:
        return None

    if "```" in text:
        text = text.replace("```json", "").replace("```JSON", "").replace("```", "").strip()

    decoder = json.JSONDecoder()
    brace_positions = [i for i, ch in enumerate(text) if ch == "{"]
    for pos in reversed(brace_positions):
        try:
            obj, _ = decoder.raw_decode(text[pos:])
            if isinstance(obj, dict) and ("summary" in obj or "status" in obj or "keywords" in obj):
                return obj
        except json.JSONDecodeError:
            continue

    for pos in reversed(brace_positions):
        try:
            obj, _ = decoder.raw_decode(text[pos:])
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue

    return None


def analyze_text(text: str) -> dict[str, Any]:
    if not text or not text.strip():
        return _error_response("輸入內容為空，請提供有效文字。")

    api_key = os.getenv("NVIDIA_API_KEY", "").strip()
    if not api_key:
        return _error_response("缺少 NVIDIA_API_KEY 環境變數，請檢查 .env 設定。")

    client = OpenAI(
        base_url=BASE_URL,
        api_key=api_key,
        timeout=90.0,
        max_retries=0,
    )

    last_error = ""
    for _ in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                temperature=0.2,
                max_tokens=4096,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"請分析以下內容：\n\n{text.strip()}"},
                ],
            )
        except Exception as e:
            return _error_response(f"NVIDIA NIM API 呼叫失敗：{e}")

        msg = response.choices[0].message
        content_text = (msg.content or "").strip()
        reasoning_text = (getattr(msg, "reasoning_content", None) or "").strip()

        parsed = _parse_json_object(content_text) or _parse_json_object(reasoning_text)
        if isinstance(parsed, dict):
            chosen_raw = content_text if _parse_json_object(content_text) else reasoning_text
            normalized = _normalize_result(parsed, chosen_raw)
            has_content = bool(normalized["summary"]) and (
                bool(normalized["keywords"]) or bool(normalized["complex_sentences"])
            )
            if has_content:
                return normalized
            last_error = f"模型回傳內容不完整（摘要或解析欄位為空） | 原始輸出：{chosen_raw[:300]}"
            continue

        preview = (content_text or reasoning_text)[:300]
        last_error = f"JSON 解析失敗：無法擷取完整 JSON 物件 | 原始輸出：{preview}"

    return _error_response(last_error or "未知解析錯誤。")