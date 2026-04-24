from __future__ import annotations
import sys

import yaml
import re
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
from dotenv import load_dotenv
import fitz

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
def build_zero_shot_prompt(chunk: str) -> str:
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
# FEW-SHOT PROMPT
# =========================
def build_few_shot_prompt(chunk: str) -> str:
    return f"""
Extract Key Data Elements (KDEs) and their requirements.

Example:
user_authentication:
  name: User Authentication
  requirements:
    - Must use multi-factor authentication
    - Passwords must be at least 12 characters

Now extract from the following text:

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
# CHAIN OF THOUGHT PROMPT
# =========================
def build_chain_of_thought_prompt(chunk: str) -> str:
    return f"""
Extract Key Data Elements (KDEs) and their requirements.

Think step-by-step:
1. Identify potential KDEs mentioned in the text.
2. For each KDE, determine what requirements are specified.
3. Ensure requirements are clear and non-empty.

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
# Run LLM
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
def process_file(file_path, tokenizer, model, prompt_builder=build_zero_shot_prompt, prompt_type="zero-shot"):
    print(f"\nProcessing {file_path} with {prompt_type}...")

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_text(text)
    print(f"Total chunks: {len(chunks)}")

    parsed_outputs = []
    prompt_log_parts = []
    raw_output_log_parts = []

    for i, chunk in enumerate(chunks):
        chunk_number = i + 1
        print(f"Chunk {chunk_number}/{len(chunks)}")

        prompt = prompt_builder(chunk)

        prompt_log_parts.append(
            f"=== Chunk {chunk_number}/{len(chunks)} Prompt ===\n{prompt}"
        )

        raw_output = run_llm(prompt, tokenizer, model)

        raw_output_log_parts.append(
            f"=== Chunk {chunk_number}/{len(chunks)} LLM Output ===\n{raw_output}"
        )

        print(
            "Output preview:",
            raw_output[:200].encode("utf-8", errors="ignore").decode()
        )

        yaml_text = extract_yaml(raw_output)

        data = parse_yaml(yaml_text)
        if data:
            parsed_outputs.append(data)
        else:
            print("⚠️ Skipped invalid YAML chunk")

    safe_prompt_type = prompt_type.replace(" ", "-").replace("_", "-").lower()

    output_log_file = (
        str(file_path)
        .replace(".txt", f"-{safe_prompt_type}-llm-output.txt")
        .replace(".pdf", f"-{safe_prompt_type}-llm-output.txt")
    )

    write_llm_output_log(
        output_file=output_log_file,
        llm_name="google/gemma-3-1b-it",
        prompt_type=prompt_type,
        prompt_used="\n\n".join(prompt_log_parts),
        llm_output="\n\n".join(raw_output_log_parts),
    )

    merged = merge_kdes(parsed_outputs)
    return merged

# =========================
# SAVE YAML
# =========================
def save_yaml(data, input_file, prompt_type="zero-shot"):
    safe_prompt_type = prompt_type.replace(" ", "-").replace("_", "-").lower()

    output_file = (
        input_file
        .replace(".txt", f"-{safe_prompt_type}-kdes.yaml")
        .replace(".pdf", f"-{safe_prompt_type}-kdes.yaml")
    )

    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

    print(f"Saved: {output_file}")
    return output_file

# =========================
# CONVERT PDF TO TXT
# =========================
def pdf_to_txt(pdf_path: str) -> str:
    """
    Convert PDF to text, save as .txt in same folder, and return the text content.
    """

    pdf_path = os.path.join("data", pdf_path)

    # Open PDF
    doc = fitz.open(pdf_path)

    # Extract text from all pages
    text = ""
    for page in doc:
        text += page.get_text()

    # Close PDF
    doc.close()

    # Create output path (same folder, replace .pdf with .txt)
    txt_path = pdf_path.replace(".pdf", ".txt")

    # Save text to file
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Converted {pdf_path} to {txt_path}")

    return text

# =========================
# WRITE TASK-1 LLM OUTPUT LOG
# =========================


def write_llm_output_log(
    output_file,
    llm_name,
    prompt_type,
    prompt_used,
    llm_output,
):
    from pathlib import Path

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = (
        "*LLM Name*\n"
        f"{llm_name}\n\n"
        "*Prompt Used*\n"
        f"{prompt_used}\n\n"
        "*Prompt Type*\n"
        f"{prompt_type}\n\n"
        "*LLM Output*\n"
        f"{llm_output}\n"
    )

    output_path.write_text(content, encoding="utf-8")
    return output_path


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

    prompt_runs = [
        ("zero-shot", build_zero_shot_prompt),
        ("few-shot", build_few_shot_prompt),
        ("chain-of-thought", build_chain_of_thought_prompt),
    ]

    for file in files:
        for prompt_type, prompt_builder in prompt_runs:
            result = process_file(
                file_path=file,
                tokenizer=tokenizer,
                model=model,
                prompt_builder=prompt_builder,
                prompt_type=prompt_type,
            )

            save_yaml(
                data=result,
                input_file=file,
                prompt_type=prompt_type,
            )