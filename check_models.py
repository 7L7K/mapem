#!/usr/bin/env python3
"""
check_models.py – list your org‑approved models and flag the big ones
"""

import os
from openai import OpenAI, OpenAIError

# Grab creds straight from env (direnv already exports ‘em)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    organization=os.getenv("OPENAI_ORG_ID"),
)

# Models we care about right now
candidates = [
    "o3",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4o-high",
    "gpt-4-turbo",
    "gpt-4o-128k",
]

def normalize(model_id: str) -> str:
    """
    API returns full versions like `gpt-4o-mini-2025-04-09`.
    Strip the date suffix so we can match against the short names above.
    """
    for c in candidates:
        if model_id.startswith(c):
            return c
    return model_id  # leave others untouched

try:
    raw_models = client.models.list().data
    available = {normalize(m.id) for m in raw_models}

    print("\n🔍  Model availability check:")
    for name in candidates:
        print(f"{'✅' if name in available else '❌'} {name}")

    # Show a trimmed dump in case you want the exact version strings
    print("\n📋  Full list (trimmed to 30 IDs):")
    for m in sorted([m.id for m in raw_models])[:30]:
        print(" •", m)

except OpenAIError as err:
    print("🚨  API call failed:", err)
