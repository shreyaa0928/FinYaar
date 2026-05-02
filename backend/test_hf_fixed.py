"""
test_hf_fixed.py  –  FinYaar | HF API Token Validator
Run: python test_hf_fixed.py
"""
import os, requests, json
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('HF_API_KEY', '')

if not token:
    print("❌ HF_API_KEY not set in .env file!")
    print("   Add:  HF_API_KEY=hf_xxxxxxxxxxxx")
    exit(1)

print(f"🔑 Token: {token[:10]}...")

# ── Correct endpoint (NOT the router URL) ──────────────────
MODEL  = "mistralai/Mistral-7B-Instruct-v0.2"
URL = f"https://router.huggingface.co/hf-inference/models/{MODEL}/v1/chat/completions"

headers = {"Authorization": f"Bearer {token}"}
payload = {
    "model": "mistralai/Mistral-7B-Instruct-v0.2",
    "messages": [
        {"role": "user", "content": "What is SIP? Explain in one sentence."}
    ],
    "max_tokens": 80
}

print(f"📡 Sending request to: {URL}")
resp = requests.post(URL, headers=headers, json=payload, timeout=40)

print(f"📊 Status Code: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    text = data[0]['generated_text'] if data else "(empty)"
    print(f"✅ SUCCESS! Model response:\n   {text.strip()}")

elif resp.status_code == 503:
    print("⏳ Model is still loading on HF servers.")
    print("   Wait 20–30 seconds and try again. This is normal for free tier.")

elif resp.status_code == 401:
    print("❌ INVALID TOKEN — check your HF_API_KEY in .env")

elif resp.status_code == 403:
    print("❌ ACCESS DENIED — You need to accept Mistral's terms:")
    print("   👉 https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2")

else:
    print(f"❌ Error: {resp.text[:300]}")
