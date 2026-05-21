---
title: AI Pair Engineer
emoji: 💻
colorFrom: purple
colorTo: blue
sdk: gradio
sdk_version: 6.14.0
python_version: '3.13'
app_file: app.py
pinned: false
license: mit
short_description: A small AI that sits next to you while you write code
---

# AI Pair Engineer

> A small AI that sits next to you while you write code — detecting design flaws, proposing tests, and refactoring. Not after the fact. During.

**Live demo:** _replace this line with your HF Spaces URL after deploying_
**Repo:** _replace this line with your GitHub URL_

---

## Why this design

| Decision | Reasoning |
|---|---|
| One LLM call, not three | Multi-step agents on a free-tier inference API drift on JSON handoff. Single call with rich structured output is more reliable and ships faster. |
| Qwen 2.5 Coder 32B Instruct | Strongest code-tuned model on HF's free Inference tier. Swappable via `HF_MODEL` env var. |
| Pure JSON output, no prose | Makes the output a real interface, not a chat. Downstream tools can consume it: CI, IDE extensions, GitHub Actions. |
| `positive` field is mandatory | Forces the model to not be purely negative. A pair programmer who only criticizes burns trust. |
| 3 prepared fixtures (N+1, SQLi, mutable default) | Recruiters can click and see it work in 5 seconds. No setup. |

## Architecture

```
┌─────────────────────────────────────────┐
│ Gradio UI (HF Space)                    │
│ - paste code, pick language             │
│ - 3 fixture buttons for instant demo    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ One inference call                      │
│ - SYSTEM_PROMPT (prompt.py)             │
│ - user message: code + language         │
│ - HF Inference: Qwen 2.5 Coder 32B      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Structured JSON parser                  │
│ - summary, flaws[], tests[], refactor   │
│ - positive (mandatory)                  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ 5 tabs in UI                            │
│ - Design flaws / Tests / Refactor       │
│ - Structured JSON / Raw output          │
└─────────────────────────────────────────┘
```

## Run locally

```bash
pip install -r requirements.txt
export HF_TOKEN=hf_xxx   # optional locally; auto-injected on HF Spaces
python app.py
```

App boots at http://localhost:7860.

## Deploy to Hugging Face Spaces

```bash
# 1. Create a new Space at https://huggingface.co/new-space
#    SDK: Gradio · Hardware: CPU basic (free)

# 2. Clone the empty Space and copy in the project
git clone https://huggingface.co/spaces/<your-user>/ai-pair-engineer
cp -r ai-pair-engineer/* ai-pair-engineer/.* <hf-space-dir>/

# 3. Push
cd <hf-space-dir>
git add . && git commit -m "Initial deploy" && git push
```

Space auto-builds and provides a public URL. No environment variables needed — HF injects an inference token automatically.

## Push to GitHub (separately)

```bash
gh repo create ai-pair-engineer --public --source=. --remote=origin
git add . && git commit -m "AI Pair Engineer v0.1"
git push -u origin main
```

## Limitations (honest)

- Free-tier inference quotas: first request can cold-start at ~20s.
- Diff output sometimes has whitespace artifacts on small models. The Raw tab lets you copy the original output if the formatted view is off.
- Single-file snippets only. Multi-file context is out of scope for v0.1.
- No persistence — every review is stateless. Adding history is a one-day add (SQLite + `gr.State`).

## What v0.2 would add (not built)

- Cost-aware routing: route trivial snippets to a smaller model, complex ones to Qwen 32B
- Apply-the-diff button: confirm and the UI shows the post-refactor code
- Eval harness in `tests/eval/`: 20 known-buggy snippets, scored on which flaws were caught
- IDE extension shim: same JSON, exposed as a Cursor / VS Code language-server endpoint

## License

MIT.
