from transformers import AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv

import sys
import re
import os

import yaml
import fitz

model_name = "google/gemma-3-1b-it"
currentFile = 0  # Global variable to track current file for logging

def LoadPDF(file_path: str) -> str:
    # Construct the full path using the global folder_path
    full_path_in_drive = os.path.join("data", file_path)
    if not os.path.exists(full_path_in_drive):
        raise FileNotFoundError(f"{full_path_in_drive} not found")

    reader = fitz.open(full_path_in_drive)
    text = ""

    for page in reader:
        text += page.get_text() or ""

    if not text.strip():
        raise ValueError("Empty PDF content")

    return text

def SaveToTextFile(text: str, output_file: str) -> None:
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text)

# =========================
# Convert ALL PDF to TXT
# =========================
def TurnAllPDFIntoText():
    print(os.listdir("data"))

    for i in range(1, 5):
        print(f"Processing cis-r{i}.pdf...")
        
        if (f"cis-r{i}.txt") in os.listdir("data"):
            print(f"data/cis-r{i}.txt exists, skipping...")
            continue

        r1Out = LoadPDF(f"cis-r{i}.pdf")
        SaveToTextFile(r1Out, f"data/cis-r{i}.txt")

# =========================
# LOAD MODEL
# =========================
def load_model():
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
# ONE-SHOT PROMPT
# =========================
def build_one_shot_prompt(chunk: str) -> str:
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
def process_file(file_path, tokenizer, model):
    print(f"\nProcessing {file_path}...")

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_text(text)
    print(f"Total chunks: {len(chunks)}")

    parsed_outputs = []

    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}/{len(chunks)}")

        prompt = build_zero_shot_prompt(chunk)

        # log prompt
        AppendToFile(f"{prompt.strip()}\n", f"cis-r{currentFile}.log")
        AppendToFile(f"...\n", f"cis-r{currentFile}.log")

        # log prompt type
        AppendToFile(f"zero_shot_prompt\n", f"cis-r{currentFile}.log")
        AppendToFile(f"...\n", f"cis-r{currentFile}.log")

        output = run_llm(prompt, tokenizer, model)
        
        # log raw llm output
        AppendToFile(f"{output.strip()}\n", f"cis-r{currentFile}.log")
        AppendToFile(f"...\n", f"cis-r{currentFile}.log")

        output = extract_yaml(output)

        data = parse_yaml(output)
        if data:
            parsed_outputs.append(data)
        else:
            print("Skipped invalid YAML chunk")

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

def AppendToFile(content, filePath):
    # print(filePath)
    filePath = os.path.join("logs", filePath)
    # print(filePath)

    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    if not os.path.exists(filePath):
        # Create the file if it doesn't exist
        with open(filePath, "w", encoding="utf-8") as f:
            f.write("") # Write an empty string to create the file

    with open(filePath, "a", encoding="utf-8") as f:
        f.write(content)

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

    for i, file in enumerate(files):
        currentFile = i+1  # Set global variable for logging

        # delete log file if it exists
        if os.path.exists(f"logs/cis-r{currentFile}.log"):
            os.remove(f"logs/cis-r{currentFile}.log")

        # log model name
        AppendToFile(model_name + "\n", f"cis-r{currentFile}.log")
        AppendToFile(f"...\n", f"cis-r{currentFile}.log")

        result = process_file(file, tokenizer, model)
        save_yaml(result, file)