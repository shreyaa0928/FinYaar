import os
import requests
import json
from dotenv import load_dotenv

# Use the token from env for testing
load_dotenv()
token = os.getenv("HF_API_KEY", "")

def log(msg):
    with open('hf_test_output.txt', 'a') as f:
        f.write(msg + '\n')
        f.flush()
    print(msg)

if os.path.exists('hf_test_output.txt'): os.remove('hf_test_output.txt')

url = "https://router.huggingface.co/hf-inference/models/mistralai/Mistral-7B-Instruct-v0.2"
headers = {"Authorization": f"Bearer {token}"}

payload = {
    "inputs": "<s>[INST] What is SIP? Explain in one sentence. [/INST]",
    "parameters": {"max_new_tokens": 100}
}

try:
    log("Sending request to Hugging Face...")
    response = requests.post(url, headers=headers, json=payload, timeout=20)
    log(f"Status Code: {response.status_code}")
    log(f"Response: {response.text}")
    if response.status_code == 200:
        log("✅ Hugging Face Token is VALID!")
    else:
        log("❌ Hugging Face Token failed.")
except Exception as e:
    log(f"❌ Error: {e}")
