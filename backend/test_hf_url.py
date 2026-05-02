import os, requests, json
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('HF_API_KEY', '')

MODEL  = "meta-llama/Llama-3.1-8B-Instruct"
URL = "https://router.huggingface.co/v1/chat/completions"

headers = {"Authorization": f"Bearer {token}"}
payload = {
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [
        {"role": "user", "content": "What is SIP?"}
    ],
    "max_tokens": 80
}

resp = requests.post(URL, headers=headers, json=payload, timeout=20)
print(f"Status Code: {resp.status_code}")
if resp.status_code == 200:
    print(resp.json())
else:
    print(resp.text)
