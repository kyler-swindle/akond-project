import yaml
import re
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv

# =========================
# CHECK GPU
# =========================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

if device.type == "cuda":
    print("GPU:", torch.cuda.get_device_name(0))

# =========================
# LOAD MODEL (Gemma)
# =========================
model_name = "google/gemma-3-1b-it"

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

tokenizer = AutoTokenizer.from_pretrained(model_name, token=HF_TOKEN)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    token=HF_TOKEN,
    torch_dtype=torch.float16 if device.type == "cuda" else torch.float32
).to(device)  # 🚨 FORCE GPU

model.eval()

# verify model device
print("Model loaded on:", next(model.parameters()).device)

# =========================
# ZERO-SHOT PROMPT
# =========================
def zero_shot_prompt(text: str) -> str:
    return f"""
Extract Key Data Elements (KDEs) and their requirements from the text.

Return ONLY valid YAML.

Format:
element1:
  name: <KDE name>
  requirements:
    - <requirement>

Rules:
- No markdown
- No ```yaml blocks
- No empty requirements
- No explanations

TEXT:
{text}
"""

# =========================
# RUN LLM
# =========================
def run_llm(prompt: str) -> str:
    inputs = tokenizer(prompt, return_tensors="pt")

    # 🚨 move tensors to GPU
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.5,
            do_sample=True,
            eos_token_id=tokenizer.eos_token_id
        )

    generated_tokens = outputs[0][inputs["input_ids"].shape[-1]:]
    return tokenizer.decode(generated_tokens, skip_special_tokens=True)

# =========================
# CLEAN OUTPUT
# =========================
def extract_yaml(text: str) -> str:
    text = text.replace("\\n", "\n")
    text = text.replace("```yaml", "").replace("```", "")

    match = re.search(r"(element\d+:.*)", text, re.DOTALL)
    if match:
        text = match.group(1)

    return text.strip()

# =========================
# CLEAN KDE STRUCTURE
# =========================
def clean_kdes(kdes: dict) -> dict:
    cleaned = {}

    for key, value in kdes.items():
        if not isinstance(value, dict):
            continue

        name = str(value.get("name") or "").strip()
        reqs = value.get("requirements") or []

        if not isinstance(reqs, list):
            reqs = [reqs]

        clean_reqs = []
        for r in reqs:
            if not r:
                continue
            r = str(r).strip()
            if r.lower() in ["", "none", "null"]:
                continue
            clean_reqs.append(r)

        clean_reqs = list(set(clean_reqs))

        if name or clean_reqs:
            cleaned[key] = {
                "name": name,
                "requirements": clean_reqs
            }

    return cleaned

# =========================
# PROCESS DOCUMENT
# =========================
def process_document(text: str):
    prompt = zero_shot_prompt(text)
    output = run_llm(prompt)

    output = extract_yaml(output)

    try:
        data = yaml.safe_load(output)
        if not isinstance(data, dict):
            return {}
    except Exception as e:
        print("YAML parsing failed:", e)
        return {}

    return clean_kdes(data)

# =========================
# SAVE YAML
# =========================
def save_yaml(data, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False)

# =========================
# RUN FILES
# =========================
def process_all_documents(file_paths):
    for path in file_paths:
        print(f"Processing {path}...")

        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        result = process_document(text)

        output_name = path.replace(".txt", "-kdes.yaml").replace(".pdf", "-kdes.yaml")

        save_yaml(result, output_name)

        print(f"Saved: {output_name}")

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    files = [
        "data/cis-r1.txt",
        "data/cis-r2.txt",
        "data/cis-r3.txt",
        "data/cis-r4.txt"
    ]

    process_all_documents(files)