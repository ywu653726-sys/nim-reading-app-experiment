# 整合 NVIDIA NIM Models 之長文摘要與長難句分析模組

## 1. 環境設定
1. 安裝相依套件：
   ```bash
   pip install -r requirements.txt
   ```
2. 複製 `.env.example` 為 `.env`，並填入自己的 `NVIDIA_API_KEY`。

## 2. 呼叫方式
```python
from ai_analyzer import analyze_text

result = analyze_text("這裡填入要分析的文章內容")
```

## 3. 回傳 JSON 格式
無論成功或失敗，皆固定回傳以下 5 個欄位：
```json
{
  "status": "success",
  "summary": "核心重點摘要",
  "keywords": ["關鍵詞1", "關鍵詞2"],
  "complex_sentences": [
    {
      "original": "原句",
      "structure": "句型結構拆解",
      "plain_explanation": "白話說明"
    }
  ],
  "error_message": null
}
```
- 若輸入為空、未設定 API Key 或端點逾時，`status` 會回傳 `"error"`，錯誤原因寫在 `error_message`。
- 目前預設使用 `mistralai/mistral-large-4-1t-a52b` 免費端點，尖峰時段可能較慢或逾時，串接時請保留例外與逾時處理。