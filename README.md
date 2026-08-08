# Minimum Agent Suite

可重現、以工具與狀態協議為中心的 Minimum Agent Suite，用於比較本地 LLM 的 Agent 行為、工具使用、失敗安全、修正能力與嚴格 JSON 輸出。

> 這是經過公開發布清理的版本。模型權重、原始 server log、完整 API/tool trace、私有環境路徑與 credentials 不包含在 repository。

## 內容

- `src/agent_eval_suite.py`：24 個情境與 objective evaluator
- `src/model_eval_pilot.py`：loopback server、HTTP、GPU metrics 等共用 helper
- `src/run_suite.py`：跨 seed 執行 wrapper；每次只在 `127.0.0.1` 啟動測試 server
- `prompts/`：baseline intervention 與 system prompt 消融候選
- `docs/comprehensive-report.md`：已清理的 aggregate 測試報告

## 測試範圍

Suite 固定包含 24 個情境：

- H1–H6：誠信／證據
- C1–C4：錯誤修正
- T1–T6：工具使用
- F1–F4：失敗安全
- A1–A3：Agent workflow
- S1：嚴格 JSON 輸出

每個設定預設使用 seed `42`、`43`；每個 seed 有 220 個 objective checks。

## 需求

- Python 3.10+
- 可執行的 [`llama.cpp`](https://github.com/ggml-org/llama.cpp) `llama-server`
- 使用者自行準備的 GGUF 主模型；MTP 另需 draft GGUF
- GPU／CPU、Flash Attention 與 model-specific 依賴由使用者自行管理

本 repository 不下載、儲存或重新發布模型權重。

## 快速開始

### 不使用 MTP

```bash
python src/run_suite.py \
  --model /path/to/model.gguf \
  --server-bin /path/to/llama-server \
  --system-prompt-file prompts/system-prompt-v3.txt \
  --output-root results/local-baseline
```

### 使用 Gemma MTP

```bash
python src/run_suite.py \
  --model /path/to/main-model.gguf \
  --model-draft /path/to/mtp-draft.gguf \
  --server-bin /path/to/llama-server \
  --spec-type draft-mtp \
  --spec-draft-n-max 2 \
  --flash-attn on \
  --system-prompt-file prompts/system-prompt-v3.txt \
  --output-root results/local-gemma-mtp
```

Windows Git Bash 範例：

```bash
python src/run_suite.py \
  --model 'C:/models/main-model.gguf' \
  --model-draft 'C:/models/mtp-draft.gguf' \
  --server-bin 'C:/llama.cpp/build/bin/llama-server.exe' \
  --spec-type draft-mtp \
  --spec-draft-n-max 2 \
  --flash-attn on \
  --system-prompt-file prompts/system-prompt-v3.txt \
  --output-root results/windows-run
```

`run_suite.py` 會為每個 seed 使用不同的 loopback port，將 JSON 結果寫入 `results/`；該資料夾被 `.gitignore` 排除，避免誤上傳 raw trace。

## 已測得的公開摘要

完整數字與限制請看 [`docs/comprehensive-report.md`](docs/comprehensive-report.md)。代表性結果：

| 設定 | Aggregate | Critical | JSON | Failure safety |
|---|---:|---:|---:|---:|
| QAT Q4 + MTP baseline, nmax=4 | 89.5% | 0 | 100% | 86.1% |
| system prompt v3 + nmax=4 | 93.4% | 0 | 92.9% | 100% |
| system prompt v3 + nmax=2 | 93.2% | 0 | 100% | 100% |

目前在工具型 Agent workload 的建議設定是 `system_prompt_v3 + spec_draft_n_max=2`；這不是對所有模型或長文本 workload 的普遍保證，請以自己的 model、llama.cpp 版本與硬體重跑。

## 安全邊界

- 測試 server 只綁定 `127.0.0.1`，不應直接改用 production bind address。
- suite 中的 `delete_file` 是 sandbox evaluator 模擬，不會刪除使用者檔案。
- 未確認前的 destructive action 應由實際 tool gateway 再次阻擋，不能只依賴 prompt。
- 工具失敗、partial、not_found 或衝突資料不應被標記為 `status: "verified"`。
- 不要把 API key、token、password、SSH private key、`.env`、raw logs 或模型檔案加入 commit。

## 結果與可重現性

每個 run 應保存：

- command 與 llama.cpp 版本
- seed、model／draft hash、system prompt hash
- load time、suite elapsed、eval throughput
- 完整 JSON、tool trace 與 server log（留在 private storage）

公開報告只保留 aggregate 結果；原始 JSON 與 log 應放在不公開的儲存位置。

## License

目前未附授權條款。公開 repository 不代表自動授予再發布或商業使用權；若要採用 MIT、Apache-2.0 或其他 license，請在發布前明確加入對應 `LICENSE` 檔案。
