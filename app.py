"""AI Pair Engineer — Gradio UI on Hugging Face Spaces.

One LLM call. Three structured outputs (flaws / tests / refactor).
Free-tier HF Inference API — no separate API key required when deployed on Spaces.
"""

import json
import os
from pathlib import Path

import gradio as gr
from huggingface_hub import InferenceClient

from prompt import SYSTEM_PROMPT, build_user_prompt


MODEL = os.environ.get("HF_MODEL", "Qwen/Qwen2.5-Coder-32B-Instruct")
HF_TOKEN = os.environ.get("HF_TOKEN")  # Optional locally; auto-provided on HF Spaces.

client = InferenceClient(model=MODEL, token=HF_TOKEN)


def _extract_json(raw: str) -> dict:
    """Parse the JSON block from the model output.

    The system prompt forbids wrapping the JSON in fences, but small models
    sometimes do it anyway. We slice from the first '{' to the last '}' to
    tolerate that.
    """
    if not raw or not raw.strip():
        raise ValueError("Empty model response.")
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response.")
    return json.loads(raw[start : end + 1])


def _format_flaws(flaws: list) -> str:
    if not flaws:
        return "_No design flaws detected._"
    blocks = []
    for f in flaws:
        line = f.get("line")
        line_str = f"line {line}" if line is not None else "no specific line"
        blocks.append(
            f"### {f.get('severity', 'medium').upper()} — {f.get('title', 'Issue')}\n"
            f"_{line_str}_\n\n"
            f"{f.get('description', '')}"
        )
    return "\n\n---\n\n".join(blocks)


def _format_tests(tests: list) -> str:
    if not tests:
        return "_No test suggestions._"
    blocks = []
    for t in tests:
        blocks.append(
            f"### `{t.get('name', 'test_unnamed')}`\n"
            f"{t.get('description', '')}\n\n"
            f"```python\n{t.get('code', '')}\n```"
        )
    return "\n\n".join(blocks)


def _format_refactor(refactor: dict) -> str:
    if not refactor:
        return "_No refactor proposed._"
    return (
        f"### {refactor.get('summary', 'Proposed change')}\n\n"
        f"```diff\n{refactor.get('diff', '')}\n```\n\n"
        f"**Rationale:** {refactor.get('rationale', '')}"
    )


def review_code(code: str, language: str) -> tuple[str, str, str, str, str]:
    """Run one LLM call and return five rendered panels."""
    if not code or not code.strip():
        return ("Please paste some code first.", "", "", "", "")

    try:
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(code, language)},
            ],
            max_tokens=2048,
            temperature=0.2,
        )
        raw = response.choices[0].message.content
    except Exception as e:
        return (f"Inference error: {e}", "", "", "", "")

    try:
        data = _extract_json(raw)
    except (ValueError, json.JSONDecodeError) as e:
        return (
            f"Failed to parse model output as JSON ({e}). Raw output in the Raw tab.",
            "",
            "",
            "",
            raw,
        )

    summary = data.get("summary", "")
    positive = data.get("positive", "")
    header = f"**Summary:** {summary}\n\n**What's done right:** {positive}\n\n---\n\n" if summary or positive else ""

    return (
        header + _format_flaws(data.get("flaws", [])),
        _format_tests(data.get("tests", [])),
        _format_refactor(data.get("refactor", {})),
        json.dumps(data, indent=2),
        raw,
    )


# ─── UI ────────────────────────────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).parent / "tests" / "fixtures"


def _load_fixture(name: str) -> str:
    path = FIXTURES_DIR / name
    return path.read_text() if path.exists() else ""


with gr.Blocks(title="AI Pair Engineer", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # AI Pair Engineer

        Sits next to you while you write. Detects design flaws, proposes tests, refactors.
        One LLM call. JSON-structured output. Open source.

        **Stack:** Qwen 2.5 Coder via Hugging Face Inference + Gradio. No external API key needed when running on Spaces.
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            code_in = gr.Code(
                label="Paste code",
                language="python",
                lines=20,
                value=_load_fixture("n_plus_one.py"),
            )
            language_in = gr.Dropdown(
                ["python", "javascript", "typescript", "go", "java"],
                value="python",
                label="Language",
            )
            btn = gr.Button("Review with my pair", variant="primary")

            gr.Markdown("### Try a fixture")
            with gr.Row():
                gr.Button("N+1 query").click(
                    lambda: _load_fixture("n_plus_one.py"), outputs=code_in
                )
                gr.Button("SQL injection").click(
                    lambda: _load_fixture("sql_injection.py"), outputs=code_in
                )
                gr.Button("Mutable default arg").click(
                    lambda: _load_fixture("mutable_default.py"), outputs=code_in
                )

        with gr.Column(scale=1):
            with gr.Tab("Design flaws"):
                flaws_out = gr.Markdown()
            with gr.Tab("Test suggestions"):
                tests_out = gr.Markdown()
            with gr.Tab("Refactor"):
                refactor_out = gr.Markdown()
            with gr.Tab("Structured JSON"):
                json_out = gr.Code(language="json", lines=20)
            with gr.Tab("Raw model output"):
                raw_out = gr.Code(lines=20)

    btn.click(
        review_code,
        inputs=[code_in, language_in],
        outputs=[flaws_out, tests_out, refactor_out, json_out, raw_out],
    )


if __name__ == "__main__":
    demo.launch()
