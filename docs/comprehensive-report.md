# Minimum Agent Suite 綜合測試報告

> 報告生成時間：`2026-08-08T08:02:22.878934+00:00`（由遠端測試主機產生）
>

> Public-release note：模型權重、原始 comparison/report JSON、server log、完整 API/tool trace、私有遠端路徑與 retention manifest 不包含在此公開版本；本文件只保留可公開的 aggregate 結果與方法。
> 本報告彙整已完成的模型比較、Gemma 4 QAT Q4 + MTP、system prompt A/B／消融與 `spec_draft_n_max` sweep。所有分數直接取自保存的 `comparison.json`／`report.json`。

## 1. 執行摘要

目前最推薦的 Agent 部署組合是：

```text
Gemma 4 26B A4B QAT Q4_K_XL + MTP
system_prompt_v3
spec_draft_n_max=2
```

- v3 + nmax=2：`410/440`（93.2%），critical `0`，JSON `100.0%`，failure safety `100.0%`。
- v3 + nmax=4：`411/440`（93.4%），是本輪最高 aggregate 分數，但 JSON 分類為 `92.9%`。
- 若只使用原始 baseline system prompt，nmax=2／3／4 的 Agent 能力幾乎相同；nmax=2 的 end-to-end suite time 最短。
- 不論模型／prompt variant，本報告納入的 QAT Q4 MTP 與 prompt 實驗均沒有新增 critical failure。

## 2. 測試範圍與方法

- Minimum Agent Suite：24 個情境，包含 H1–H6、C1–C4、T1–T6、F1–F4、A1–A3、S1。
- 每個模型／設定使用 seed `42`、`43`；每個 seed 為 220 個 objective checks，兩 seed 合計 440 checks。
- 工具型 case 保存完整 API trace、tool trace、最終輸出、評分 checks 與 server log。
- critical failure 包含工具失敗／不完整／衝突後仍輸出 `status:"verified"`，以及未確認就執行 `delete_file` 等安全協議錯誤。
- MTP sweep 固定主模型、draft model、temperature、top-p、max tokens、工具、GPU offload、Flash Attention 與測試情境，只改 `spec_draft_n_max`。
- system prompt 消融固定模型、MTP、seed、suite、工具與推論參數，只加入一組增量規則。

## 3. 初始模型比較

以下為已完成的非 system-prompt 模型比較；每列的 seed 欄位格式為 `passed/total`。

| 模型 | Seed 分數 | Aggregate | Critical | 平均 load 秒 | 分類平均（誠信／修正／失敗安全／Tool／Agent／JSON） |
|---|---|---:|---:|---:|---|
| `gemma4-26b-q4` | 42: 196/220, 43: 198/220 | 394/440 (89.5%) | 0 | 12.89 | 誠信 98.1% / 修正 66.7% / 失敗安全 86.1% / Tool 100.0% / Agent 83.3% / JSON 100.0% |
| `qwen36-35b-heretic-q6` | 42: 184/220, 43: 189/220 | 373/440 (84.8%) | 4 | 89.09 | 誠信 88.0% / 修正 69.4% / 失敗安全 83.3% / Tool 90.4% / Agent 85.0% / JSON 100.0% |
| `gemma4-12b-q4` | 42: 186/220, 43: 184/220 | 370/440 (84.1%) | 2 | 5.30 | 誠信 83.3% / 修正 69.4% / 失敗安全 83.3% / Tool 100.0% / Agent 70.0% / JSON 100.0% |
| `qwythos9b-q5` | 42: 182/220, 43: 185/220 | 367/440 (83.4%) | 3 | 4.12 | 誠信 87.0% / 修正 69.4% / 失敗安全 88.9% / Tool 79.8% / Agent 90.0% / JSON 100.0% |
| `qwen36-35b-mxfp4` | 42: 180/220, 43: 179/220 | 359/440 (81.6%) | 4 | 9.12 | 誠信 85.2% / 修正 69.4% / 失敗安全 80.6% / Tool 79.8% / Agent 90.0% / JSON 100.0% |
| `gemma4-26b-mxfp4` | 42: 180/220, 43: 179/220 | 359/440 (81.6%) | 3 | 10.37 | 誠信 88.0% / 修正 55.6% / 失敗安全 84.7% / Tool 100.0% / Agent 58.3% / JSON 100.0% |
| `qwen36-35b-uncensored-q8` | 42: 171/220, 43: 184/220 | 355/440 (80.7%) | 3 | 73.43 | 誠信 88.9% / 修正 69.4% / 失敗安全 76.4% / Tool 77.2% / Agent 86.7% / JSON 100.0% |
| `qwen-agentworld-35b-mxfp4` | 42: 169/220, 43: 175/220 | 344/440 (78.2%) | 0 | 13.79 | 誠信 79.6% / 修正 69.4% / 失敗安全 76.4% / Tool 77.2% / Agent 85.0% / JSON 100.0% |
| `gemma4-26b-ud-q5km` | 42: 172/220, 43: 171/220 | 343/440 (78.0%) | 0 | 6.04 | 誠信 85.2% / 修正 51.4% / 失敗安全 86.1% / Tool 89.5% / Agent 60.0% / JSON 100.0% |
| `gemma4-26b-ud-q4km` | 42: 164/220, 43: 159/220 | 323/440 (73.4%) | 4 | 4.78 | 誠信 72.2% / 修正 55.6% / 失敗安全 79.2% / Tool 86.0% / Agent 60.0% / JSON 100.0% |
| `ornith35b-mxfp4` | 42: 151/220, 43: 156/220 | 307/440 (69.8%) | 2 | 14.23 | 誠信 73.1% / 修正 69.4% / 失敗安全 72.2% / Tool 72.8% / Agent 56.7% / JSON 64.3% |
| `ornith35b-q6` | 42: 136/220, 43: 128/220 | 264/440 (60.0%) | 2 | 31.60 | 誠信 64.8% / 修正 69.4% / 失敗安全 45.8% / Tool 66.7% / Agent 51.7% / JSON 28.6% |
| `qwen35-4b-iq4-xs` | 42: 129/220, 43: 129/220 | 258/440 (58.6%) | 0 | 3.55 | 誠信 67.6% / 修正 69.4% / 失敗安全 44.4% / Tool 53.5% / Agent 46.7% / JSON 100.0% |

主要結論：

- 原 Gemma 4 26B QAT Q4 是初始比較中最強的 Agent 基準，客觀通過率約 89.5%、critical 0。
- Gemma 4 26B MXFP4_MOE 約 81.6%，有 3 個 critical failure。
- UD-Q4_K_M 約 73.4%，有 4 個 critical failure；不適合作為主要 Agent。
- UD-Q5_K_M 約 78.0%、critical 0，安全性優於 UD-Q4_K_M，但能力仍低於原 QAT Q4。

## 4. Gemma 4 QAT Q4 + MTP 驗證

### 4.1 模型與命令

- Target：`[PRIVATE_PATH_OMITTED]`
- Target size：`14,249,045,120` bytes
- Target SHA256：`dcf179a91153e3a7ece792e48ef872180d9d6ef9b7677f0a0bd3e83cfe624d5e`
- MTP draft：`[PRIVATE_PATH_OMITTED]`
- Draft size：`251,937,728` bytes
- Draft SHA256：`62bd3af7f66c9308de9a5454233852f8c7324c93767e8dfb824ed45b9179864a`

等效啟動參數：

```bash
llama-server \
  --model [PRIVATE_PATH_OMITTED] \
  --model-draft [PRIVATE_PATH_OMITTED] \
  --spec-type draft-mtp \
  --spec-draft-n-max 4 \
  --flash-attn on \
  --host 127.0.0.1 \
  --port 18810
```

Smoke test 已確認 health、Chat completion 與 MTP draft acceptance；回應曾觀測到 `draft_n=4`、`draft_n_accepted=4`。啟動時曾出現 `failed to measure draft model memory` warning，但 server 正常服務且 log 持續記錄 draft acceptance。
- 官方模型儲存庫：`https://huggingface.co/unsloth/gemma-4-26B-A4B-it-qat-GGUF`。

### 4.2 MTP baseline 與未使用 MTP 比較

| 實驗 | Seed 42 | Seed 43 | Aggregate | Critical | 平均 suite 秒 | 平均 load 秒 | Draft acceptance | Eval tok/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| QAT Q4 + MTP, nmax=4 | 202/220 | 192/220 | 394/440 (89.5%) | 0 | 58.76 | 3.52 | 54.0% | 326.5 |

- QAT Q4 + MTP aggregate：89.5%，critical 0。
- 與先前未使用 MTP 的同一 QAT Q4 aggregate 89.5%、critical 0 相同。
- 未使用 MTP：seed 42 為 89.1%、suite 190.5 秒、eval 96.0 tok/s；seed 43 為 90.0%、suite 223.3 秒、eval 85.4 tok/s。
- MTP baseline 的 suite elapsed 約 58–59 秒；先前未使用 MTP 的同一 QAT Q4 約 190–223 秒。
- MTP 的速度結果是 server log 的 eval throughput 與整體 suite elapsed，不是由檔案大小推論。

## 5. System prompt 實驗

### 5.1 長版 v2 與精簡版 v3

| 實驗 | Seed 42 | Seed 43 | Aggregate | Critical | 平均 suite 秒 | 平均 load 秒 | Draft acceptance | Eval tok/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline system prompt | 202/220 | 192/220 | 394/440 (89.5%) | 0 | 58.76 | 3.52 | 54.0% | 326.5 |
| system_prompt_v2（長版） | 153/220 | 171/220 | 324/440 (73.6%) | 0 | 62.59 | 3.35 | 52.6% | 281.4 |
| system_prompt_v3（精簡版） | 205/220 | 206/220 | 411/440 (93.4%) | 0 | 56.68 | 3.53 | 54.6% | 342.9 |
| system_prompt_v3 + nmax=2 | 204/220 | 206/220 | 410/440 (93.2%) | 0 | 56.38 | 3.53 | 70.5% | 346.3 |

分類結果：

| Variant | 誠信 | 修正 | 失敗安全 | Tool | Agent | JSON |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 98.1% | 66.7% | 86.1% | 100.0% | 83.3% | 100.0% |
| v2 | 66.7% | 69.4% | 93.1% | 71.9% | 81.7% | 28.6% |
| v3 | 100.0% | 69.4% | 100.0% | 100.0% | 90.0% | 92.9% |
| v3+nmax2 | 98.1% | 69.4% | 100.0% | 100.0% | 90.0% | 100.0% |

觀察：

- v2 長版：73.6%，大量出現 Markdown code fence 與 JSON 檢查失敗；不是有效 intervention。
- v3 精簡版：93.4%，誠信與失敗安全達 100%，Agent workflow 90%，但有一個 structured-output 失分。
- v3+nmax2：93.2%，JSON 回到 100%，failure safety 100%，critical 0；是較穩定的實際部署折衷。

### 5.2 單規則消融

| 實驗 | Seed 42 | Seed 43 | Aggregate | Critical | 平均 suite 秒 | 平均 load 秒 | Draft acceptance | Eval tok/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| JSON-only | 205/220 | 205/220 | 410/440 (93.2%) | 0 | 57.10 | 3.52 | 53.3% | 337.6 |
| status-only | 197/220 | 197/220 | 394/440 (89.5%) | 0 | 57.63 | 3.53 | 53.7% | 337.4 |
| confirmation-only | 196/220 | 201/220 | 397/440 (90.2%) | 0 | 56.60 | 3.78 | 51.6% | 342.7 |
| correction-only | 191/220 | 190/220 | 381/440 (86.6%) | 0 | 61.30 | 3.77 | 54.2% | 324.3 |

| Variant | Aggregate | 相對 baseline | 誠信 | 修正 | 失敗安全 | Agent | JSON |
|---|---:|---:|---:|---:|---:|---:|---:|
| JSON-only | 93.2% | +3.6 pp | 98.1% | 69.4% | 100.0% | 90.0% | 100.0% |
| status-only | 89.5% | +0.0 pp | 100.0% | 63.9% | 86.1% | 83.3% | 100.0% |
| confirmation-only | 90.2% | +0.7 pp | 97.2% | 66.7% | 86.1% | 90.0% | 100.0% |
| correction-only | 86.6% | -3.0 pp | 92.6% | 63.9% | 86.1% | 75.0% | 100.0% |

消融結論：

- JSON-only 是最穩定的單一增量：93.2%、JSON 100%、failure safety 100%、critical 0。
- status-only 提升 honesty，但 aggregate 沒有提升，且 correction 有回落。
- confirmation-only 只有輕微 aggregate 改善，不能取代外部 delete gate。
- correction-only 反而降至 86.6%，表示目前 correction 問題不能只靠增加文字規則解決。
- 長短不是唯一因果；規則重複、輸出限制與模型注意力競爭同樣重要。

### 5.3 system prompt 限制

本 A/B 實驗使用 suite 的 baseline system prompt 與工具 schema，不等同於完整 Hermes 生產環境中同時載入 Soul.md、所有 tool 說明與所有 skill 內容。因此結果支持「精簡、按需載入、避免重複」的設計方向，但不能直接把這些分數宣稱為完整 Hermes prompt 的分數。

## 6. `spec_draft_n_max` sweep

### 6.1 原始 baseline system prompt

| 實驗 | Seed 42 | Seed 43 | Aggregate | Critical | 平均 suite 秒 | 平均 load 秒 | Draft acceptance | Eval tok/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| nmax=1 | 196/220 | 197/220 | 393/440 (89.3%) | 0 | 59.01 | 3.17 | 79.9% | 319.9 |
| nmax=2 | 202/220 | 191/220 | 393/440 (89.3%) | 0 | 55.77 | 3.17 | 69.6% | 342.6 |
| nmax=3 | 196/220 | 198/220 | 394/440 (89.5%) | 0 | 56.22 | 3.60 | 62.6% | 343.7 |
| nmax=4 | 202/220 | 192/220 | 394/440 (89.5%) | 0 | 58.76 | 3.52 | 54.0% | 326.5 |

nmax sweep 的分類摘要：

| nmax | 誠信 | 修正 | 失敗安全 | Tool | Agent | JSON |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 97.2% | 66.7% | 86.1% | 100.0% | 83.3% | 100.0% |
| 2 | 97.2% | 66.7% | 86.1% | 100.0% | 83.3% | 100.0% |
| 3 | 98.1% | 66.7% | 86.1% | 100.0% | 83.3% | 100.0% |
| 4 | 98.1% | 66.7% | 86.1% | 100.0% | 83.3% | 100.0% |

觀察：

- nmax=1 的 draft acceptance 最高，但整體 suite 最慢，不值得作為主要設定。
- nmax=2 的平均 suite time 最短，Agent aggregate 與 nmax=4 只差一個 objective check，critical 仍為 0。
- nmax=3 的 raw eval throughput 略高，但沒有帶來整體 suite 的優勢。
- nmax=4 是模型卡範例值，但在這個多工具、短回合 Agent workload 沒有比 nmax=2 更快或更安全。
- Draft acceptance ratio 會隨 nmax 增大而下降；不能單獨用 acceptance ratio 選設定，應看 end-to-end latency 與 Agent score。

### 6.2 v3 prompt interaction check

| 實驗 | Seed 42 | Seed 43 | Aggregate | Critical | 平均 suite 秒 | 平均 load 秒 | Draft acceptance | Eval tok/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v3 + nmax=2 | 204/220 | 206/220 | 410/440 (93.2%) | 0 | 56.38 | 3.53 | 70.5% | 346.3 |
| v3 + nmax=4 | 205/220 | 206/220 | 411/440 (93.4%) | 0 | 56.68 | 3.53 | 54.6% | 342.9 |

v3 interaction 的結果支持在目前 Agent workload 採用 nmax=2：JSON 100%、failure safety 100%、critical 0，整體 suite time 與 nmax=4 幾乎相同，server eval throughput 略高。

## 7. 最終建議

### 7.1 Agent 部署

```bash
--spec-type draft-mtp
--spec-draft-n-max 2
--flash-attn on
```

搭配 `system_prompt_v3`，目前實測為 93.2%、critical 0、JSON 100%、failure safety 100%。

### 7.2 模型選擇

- 主要 Agent：Gemma 4 26B QAT Q4_K_XL + MTP。
- 記憶體／速度次選：UD-Q5_K_M，但能力低於 QAT Q4。
- 不建議把 UD-Q4_K_M 作為主要安全 Agent，因為曾有 4 次 critical failure。
- MXFP4_MOE 載入較快，但曾有 3 次 critical failure，不能只看速度。

### 7.3 安全邊界

- `delete_file` 必須由外部 tool gateway 在未確認時直接阻擋。
- 工具回傳失敗、partial、not_found 或衝突時，應由 evaluator／middleware 強制禁止 `status:"verified"`。
- system prompt 可提高遵循率，但不能取代外部 validator。

## 8. 完整性、隔離與限制

- QAT target SHA256 在 MTP、nmax 與 prompt 實驗中一致：`dcf179a91153e3a7ece792e48ef872180d9d6ef9b7677f0a0bd3e83cfe624d5e`。
- MTP draft SHA256 一致：`62bd3af7f66c9308de9a5454233852f8c7324c93767e8dfb824ed45b9179864a`。
- 所有納入的 scored run 都完成 24 case、兩個 seed，並保存 API/tool trace。
- 本次 prompt／nmax 測試 ports 已釋放：`18840–18847`、`18850–18855`、`18860–18861`。
- 報告生成時 loopback `8080` 狀態為 `connect_ex=0`（仍有正式服務監聽）；測試沒有重啟或切換正式服務。
- 測試 port 上仍存在的 llama-server process：`無`。
- 未在結果或報告中保存 API key、token、password、SSH 私鑰或連線憑證。

限制：

- 每個設定只有 seed 42/43，適合工程決策，不足以作為完整統計顯著性結論。
- `spec_draft_n_max>4` 沒有驗證，不應直接套用。
- MTP throughput 來自 llama.cpp server log 的 eval time；不是完整網路端到端 tok/s benchmark。
- system prompt A/B 沒有完整重現所有 Hermes Soul／skill context。
- 任何正式服務切換、模型清理或 production 改動都不包含在本報告交付範圍。

## 9. Artifact 索引

- `prompts/system-prompt-v2.txt`
- `prompts/system-prompt-v3.txt`
- `prompts/system-prompt-ab-json.txt`
- `prompts/system-prompt-ab-status.txt`
- `prompts/system-prompt-ab-confirmation.txt`
- `prompts/system-prompt-ab-correction.txt`

---

報告結束。
