
import yaml
import re
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
from dotenv import load_dotenv

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
    device_map="auto"
)

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
# CLEAN LLM OUTPUT (IMPORTANT FIX)
# =========================
def extract_yaml(text: str) -> str:
    # fix escaped newlines
    text = text.replace("\\n", "\n")

    # remove markdown fences
    text = text.replace("```yaml", "")
    text = text.replace("```", "")

    # try extracting yaml block if embedded
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

        # remove duplicates
        clean_reqs = list(set(clean_reqs))

        if name or clean_reqs:
            cleaned[key] = {
                "name": name,
                "requirements": clean_reqs
            }

    return cleaned

# =========================
# PROCESS ONE DOCUMENT
# =========================
def process_document(text: str):
    print("Processing full document...")

    prompt = zero_shot_prompt(text)
    output = run_llm(prompt)

    # CLEAN OUTPUT (FIX YOUR ERROR)
    output = extract_yaml(output)

    try:
        data = yaml.safe_load(output)
        if not isinstance(data, dict):
            print("Invalid YAML structure")
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
# RUN ALL FILES
# =========================
def process_all_documents(file_paths):
    for path in file_paths:
        print(f"\nProcessing {path}...")

        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        # safety only (NOT truncation for logic, just crash prevention)
        # text = text[:30000]

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