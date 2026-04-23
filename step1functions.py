import sys

import yaml
import re
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
from dotenv import load_dotenv

# =========================
# LOAD MODEL
# =========================
def load_model():
    model_name = "google/gemma-3-1b-it"

    load_dotenv()
    HF_TOKEN = os.getenv("HF_TOKEN")

    tokenizer = AutoTokenizer.from_pretrained(model_name, token=HF_TOKEN)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        token=HF_TOKEN,
        device_map="auto"
    )

    return tokenizer, model


# =========================
# CHUNK TEXT
# =========================
def chunk_text(text, chunk_size=1500, overlap=200):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


# =========================
# ZERO-SHOT PROMPT
# =========================
def zero_shot_prompt(chunk: str) -> str:
    return f"""
Extract Key Data Elements (KDEs) and their requirements.

Return ONLY valid YAML.

Format:
element1:
  name: <KDE name>
  requirements:
    - <requirement>

Rules:
- No markdown
- Do NOT use ```yaml
- No empty requirements
- No explanations

TEXT:
{chunk}
"""


# =========================
# RUN LLM
# =========================
def run_llm(prompt, tokenizer, model):
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
# CLEAN OUTPUT
# =========================
def extract_yaml(text):
    text = text.replace("\\n", "\n")
    text = text.replace("```yaml", "").replace("```", "")

    match = re.search(r"(element\d+:.*)", text, re.DOTALL)
    if match:
        text = match.group(1)

    return text.strip()


# =========================
# PARSE YAML SAFELY
# =========================
def parse_yaml(output):
    try:
        data = yaml.safe_load(output)
        if isinstance(data, dict):
            return data
    except:
        return None
    return None


# =========================
# MERGE KDEs (FIXED)
# =========================
def merge_kdes(all_chunks):
    merged = {}

    for data in all_chunks:
        for _, value in data.items():

            if not isinstance(value, dict):
                continue

            name = str(value.get("name") or "").strip()
            if not name:
                continue

            reqs = value.get("requirements") or []

            if not isinstance(reqs, list):
                reqs = [reqs]

            reqs = [
                str(r).strip()
                for r in reqs
                if r and str(r).strip().lower() not in ["", "none", "null"]
            ]

            key = name.lower()  # 🔥 FIX: merge by name

            if key not in merged:
                merged[key] = {
                    "name": name,
                    "requirements": set(reqs)
                }
            else:
                merged[key]["requirements"].update(reqs)

    # convert sets → lists
    for k in merged:
        merged[k]["requirements"] = list(merged[k]["requirements"])

    return merged


# =========================
# PROCESS FILE
# =========================
def process_file(file_path, tokenizer, model):
    print(f"\nProcessing {file_path}...")

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_text(text)
    print(f"Total chunks: {len(chunks)}")

    parsed_outputs = []

    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}/{len(chunks)}")

        prompt = zero_shot_prompt(chunk)
        output = run_llm(prompt, tokenizer, model)

        # SAFE PRINT (no crash)
        print("Output preview:", output[:200].encode("utf-8", errors="ignore").decode())

        output = extract_yaml(output)

        data = parse_yaml(output)
        if data:
            parsed_outputs.append(data)
        else:
            print("⚠️ Skipped invalid YAML chunk")

    merged = merge_kdes(parsed_outputs)
    return merged


# =========================
# SAVE YAML
# =========================
def save_yaml(data, input_file):
    output_file = input_file.replace(".txt", "-kdes.yaml").replace(".pdf", "-kdes.yaml")

    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

    print(f"Saved: {output_file}")


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    tokenizer, model = load_model()

    files = [
        "data/cis-r1.txt",
        "data/cis-r2.txt",
        "data/cis-r3.txt",
        "data/cis-r4.txt"
    ]

    for file in files:
        result = process_file(file, tokenizer, model)
        save_yaml(result, file)