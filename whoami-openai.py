#!/usr/bin/env python3
import os
import yaml
from openai import OpenAI
from pathlib import Path
from pprint import pprint

print("\n🔍 Checking OpenAI client setup...\n")

# ── Load ~/.openai/config.yaml ───────────────────────────────────────
config_path = Path.home() / ".openai" / "config.yaml"
config = {}
if config_path.exists():
    with open(config_path, "r") as f:
        config = yaml.safe_load(f) or {}

# ── Load credentials ─────────────────────────────────────────────────
api_key = os.getenv("OPENAI_API_KEY") or config.get("OPENAI_API_KEY")
org_id  = os.getenv("OPENAI_ORG_ID")  or config.get("OPENAI_ORG_ID")

# ── Status printout ──────────────────────────────────────────────────
print(f"📂 Config file path: {config_path if config_path.exists() else '❌ Not found'}")
print(f"🔑 API Key: {api_key[:12] + '...' if api_key else '⛔ Not set'}")
print(f"🏢 Org ID : {org_id or '⛔ Not set'}\n")

if not api_key:
    print("❌ No API key found. Set it via ENV or config.yaml.")
    exit(1)

# ── Init client with working variables ───────────────────────────────
try:
    client = OpenAI(api_key=api_key, organization=org_id)
    models = client.models.list()
    print("✅ Connection successful! Models:")
    pprint([m.id for m in models.data])
except Exception as e:
    print("❌ Error while accessing OpenAI:")
    print(e)
