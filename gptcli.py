#!/usr/bin/env python3
"""
GPT‑CLI 2.0  –  Codex‑style power tool for King 👑

Highlights
──────────
• ✅  OpenAI SDK v1.x  •  🔄  Streaming / live tokens
• 🛡  --dry‑run / --patch / --auto safety modes
• 📄  Multi‑context support  •  📈  Cost + token analytics
• 🐙  Optional git diff preview  •  🔧  Easily extend model rates
"""

from __future__ import annotations

import argparse, difflib, json, os, sys, textwrap
from datetime import datetime
from pathlib import Path
from typing import List

from openai import OpenAI            # ← NEW SDK import
from rich.console import Console     # pretty printing
from rich.progress import Progress   # live streaming bar
from rich.syntax import Syntax       # code highlighting
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    organization=os.getenv("OPENAI_ORG_ID")
)

# ── Config ──────────────────────────────────────────────────────────
MODEL_RATES = {
    "gpt-4o":       {"input": 5e-7,  "output": 1.5e-6},
    "gpt-4.1":      {"input": 2e-6,  "output": 8e-6},
    "gpt-4.1-mini": {"input": 5e-7,  "output": 2e-6},
    "o3":           {"input": 2e-7,  "output": 6e-7},
}
DEFAULT_RATE      = {"input": 1e-6, "output": 4e-6}
DEFAULT_MODEL     = "gpt-4o"
DEFAULT_TEMP      = 0.3
DEFAULT_CONTEXT   = Path("~/mapem/mapem_context.md").expanduser()
LOG_PATH          = Path("~/.gptcli_usage.log").expanduser()
BACKUP_FMT        = "%Y%m%d_%H%M%S"

console = Console(highlight=False)

client = OpenAI()   # ← uses env var OPENAI_API_KEY

# ── Helpers ─────────────────────────────────────────────────────────
def slurp(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[red]❌  Error reading {path}: {e}")
        sys.exit(1)

def backup(path: Path) -> Path:
    ts   = datetime.now().strftime(BACKUP_FMT)
    copy = path.with_suffix(path.suffix + f".bak.{ts}")
    path.rename(copy)
    return copy

def write_usage(entry: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.open("a", encoding="utf-8").write(json.dumps(entry) + "\n")

def rate_for(model: str) -> dict:
    return MODEL_RATES.get(model, DEFAULT_RATE)

def cost_calc(tokens_in: int, tokens_out: int, model: str) -> float:
    r = rate_for(model)
    return tokens_in * r["input"] + tokens_out * r["output"]

def show_diff(old: str, new: str, path: Path) -> None:
    diff = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=str(path),
        tofile=f"{path} (updated)",
    )
    console.print(Syntax("".join(diff), "diff"))

# ── CLI ─────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="gptcli",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """\
            ChatGPT Codex‑style CLI with auto‑apply, diff, cost tracking, and streaming.

            Example:
              gptcli -m "Refactor to async" --auto backend/api.py frontend/src/*.jsx
            """
        ),
    )
    p.add_argument("files", nargs="+", help="Target code files / globs")
    p.add_argument("-m", "--message", required=True, help="Prompt message")
    p.add_argument("-c", "--context", action="append",
                   default=[str(DEFAULT_CONTEXT)], help="Extra context file(s)")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("-t", "--temperature", type=float, default=DEFAULT_TEMP)
    p.add_argument("--stream", action="store_true", help="Stream output tokens live")
    p.add_argument("--dry-run", action="store_true",
                   help="Show response but do NOT write files")
    p.add_argument("--patch", action="store_true",
                   help="Show unified diff; ask before apply")
    p.add_argument("--auto", action="store_true", help="Overwrite files automatically")
    return p.parse_args()

def glob_paths(patterns: List[str]) -> List[Path]:
    paths = []
    for pat in patterns:
        for path in Path().glob(pat):
            paths.append(path)
    if not paths:
        console.print("[red]❌  No matching files.")
        sys.exit(1)
    return paths

# ── GPT Call ────────────────────────────────────────────────────────
def call_gpt(prompt: str, model: str, temp: float, stream: bool):
    msgs = [
        {"role": "system",
         "content": "You are a senior software engineer. Respond ONLY with the updated file content. No extra text."},
        {"role": "user", "content": prompt},
    ]

    if stream:
        out_chunks = []
        with Progress() as progress:
            task = progress.add_task("[green]Generating...", total=None)
            for chunk in client.chat.completions.create(
                model=model,
                messages=msgs,
                temperature=temp,
                stream=True,
            ):
                delta = chunk.choices[0].delta.content or ""
                console.print(delta, end="")
                out_chunks.append(delta)
            progress.update(task, completed=100)
        console.print()  # newline
        resp = "".join(out_chunks)
        usage = {"prompt_tokens": 0, "completion_tokens": 0}  # streaming: no usage stats yet
    else:
        resp = client.chat.completions.create(
            model=model,
            messages=msgs,
            temperature=temp,
        )
        usage = resp.usage.model_dump()  # {'prompt_tokens':…, 'completion_tokens':…}
        resp = resp.choices[0].message.content
    return resp, usage

# ── Main ────────────────────────────────────────────────────────────
def main() -> None:
    args  = parse_args()
    paths = glob_paths(args.files)

    # Build mega‑prompt
    ctx = "\n\n".join(slurp(Path(c)) for c in args.context)
    files_blob = "\n\n".join(f"### File: {p}\n{slurp(p)}" for p in paths)
    full_prompt = f"{ctx}\n\n{args.message.strip()}\n\n{files_blob}"

    console.print(f"[cyan]🤖  Model:[/] {args.model} / Temp {args.temperature}")
    reply, usage = call_gpt(full_prompt, args.model, args.temperature, args.stream)

    # Estimate cost (streaming returns empty usage)
    tokens_in  = usage.get("prompt_tokens", 0)
    tokens_out = usage.get("completion_tokens", 0)
    cost = cost_calc(tokens_in, tokens_out, args.model)
    console.print(f"\n📊  Tokens: {tokens_in} in / {tokens_out} out  |  💰 Cost ≈ ${cost:.6f}")

    log_entry = {
        "ts": datetime.now().isoformat(),
        "model": args.model,
        "prompt": args.message,
        "files": [str(p) for p in paths],
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost": cost,
    }
    write_usage(log_entry)

    # Decide how to apply
    if args.dry_run:
        console.print("[yellow]— DRY‑RUN: no files written —")
        return

    for path in paths:
        old = slurp(path)
        new = reply

        if args.patch or (not args.auto):
            show_diff(old, new, path)
            if not args.auto:
                confirm = console.input("[bold green]Apply this change? (y/N) ")
                if confirm.lower() != "y":
                    console.print(f"[grey]Skipped {path}")
                    continue

        backup_path = backup(path)
        path.write_text(new, encoding="utf-8")
        console.print(f"[green]✅  Updated {path}  (backup → {backup_path})")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted.")
