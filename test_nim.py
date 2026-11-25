import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
)

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


def analyze_text(text: str) -> dict:
    response = client.chat.completions.create(
        model="mistralai/mistral-large-4-1t-a52b",
        temperature=0.25,
        max_tokens=2048,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"請分析以下內容：\n\n{text}"},
        ],
    )

    raw_content = response.choices[0].message.content.strip()

    # 防呆：若模型仍不小心包了 ```json ... ```，先清掉再解析
    if raw_content.startswith("```"):
        lines = raw_content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw_content = "\n".join(lines).strip()

    try:
        parsed = json.loads(raw_content)
        return parsed
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "summary": "",
            "keywords": [],
            "complex_sentences": [],
            "error_message": f"JSON 解析失敗：{e}｜原始輸出：{raw_content[:300]}",
        }


if __name__ == "__main__":
    sample_text = (
        "心理語言學研究指出，句中相依成分的距離越遠、巢狀嵌入的結構越多，"
        "讀者處理句子所需的認知負荷就越高。在行動裝置螢幕較小的情境下，"
        "使用者若一次面對過長的段落與複雜句型，容易降低閱讀專注度與理解效率，"
        "因此結合大語言模型進行重點摘要與句法拆解，有助於提升行動學習體驗。"
    )

    result = analyze_text(sample_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))