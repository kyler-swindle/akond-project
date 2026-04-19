import os
import sys
from PyPDF2 import PdfReader
from transformers import AutoTokenizer, AutoModelForCausalLM

import main

model_name = "google/gemma-3-1b-it"

FOLDER_PATH = "data"
tokenizer = None
model = None
HF_TOKEN = None

def TurnAllPDFIntoText():
    print(os.listdir("data"))

    for i in range(1, 5):
        print(f"Processing cis-r{i}.pdf...")
        
        if (f"cis-r{i}.txt") in os.listdir("data"):
            print(f"{FOLDER_PATH}/cis-r{i}.txt exists, skipping...")
            continue

        r1Out = LoadPDF(f"cis-r{i}.pdf")
        SaveToTextFile(r1Out, f"{FOLDER_PATH}/cis-r{i}.txt")

def SaveToTextFile(text: str, output_file: str) -> None:
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text)

def LoadPDF(file_path: str) -> str:
    # Construct the full path using the global folder_path
    full_path_in_drive = os.path.join(FOLDER_PATH, file_path)
    if not os.path.exists(full_path_in_drive):
        raise FileNotFoundError(f"{full_path_in_drive} not found")

    reader = PdfReader(full_path_in_drive)
    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    if not text.strip():
        raise ValueError("Empty PDF content")

    return text

def LoadTextFromFile(filePath: str) -> str:
    fullPath = os.path.join(FOLDER_PATH, filePath)
    print(fullPath)
    if not os.path.exists(fullPath):
        return ""

    with open(fullPath, "r", encoding="utf-8") as f:
        return f.read()

# Prompts
def build_zero_shot_prompt(chunk1: str, chunk2: str) -> str:
    return f"""
You are a security analyst.

Task:
Extract Key Data Elements (KDEs) from TWO document chunks.

IMPORTANT RULES:
- Treat Document 1 and Document 2 separately
- Do NOT merge KDEs across documents
- Only use provided chunks (not full documents)
- Requirements must be atomic and precise

OUTPUT FORMAT (STRICT YAML):

doc1:
  element1:
    name:
    requirements:
      - 

doc2:
  element1:
    name:
    requirements:
      - 

DOCUMENT 1 CHUNK:
{chunk1}

DOCUMENT 2 CHUNK:
{chunk2}

Return ONLY valid YAML.
"""

def build_few_shot_prompt(chunk1: str, chunk2: str) -> str:
    return f"""
You are a security requirements analyst.

Example:

Document:
"Passwords must be at least 8 characters"

Output:
doc1:
  Password Policy:
    requirements:
      - Minimum 8 characters

---

Now extract KDEs from TWO document chunks.

RULES:
- Do not merge documents
- Process only given chunks
- Keep naming consistent

OUTPUT FORMAT:

doc1:
  element1:
    name:
    requirements:

doc2:
  element1:
    name:
    requirements:

DOC1 CHUNK:
{chunk1}

DOC2 CHUNK:
{chunk2}
"""

def cot_prompt(chunk1: str, chunk2: str) -> str:
    return f"""
You are a security requirements analyst.

Your task is to extract Key Data Elements (KDEs) and their associated requirements
from TWO input documents.

Follow these steps internally:
1. Identify important security-related concepts in both documents.
2. Group related concepts into key data elements (KDEs).
3. Extract all requirements associated with each KDE.
4. Remove duplicates and ignore irrelevant or empty information.

STRICT RULES:
- Output ONLY valid YAML
- Do NOT include explanations or reasoning
- Do NOT include empty requirements
- Each KDE must have a name and a list of requirements

FORMAT:
element1:
  name: <KDE name>
  requirements:
    - <requirement 1>
    - <requirement 2>

element2:
  name: <KDE name>
  requirements:
    - <requirement>

INPUT DOCUMENT 1:
{chunk1}

INPUT DOCUMENT 2:
{chunk2}
"""

def LoadModel():
    global tokenizer, model, HF_TOKEN

    tokenizer = AutoTokenizer.from_pretrained(model_name, token=HF_TOKEN)
    model = AutoModelForCausalLM.from_pretrained(model_name, token=HF_TOKEN, device_map="auto")

def run_llm(prompt: str) -> str:
    global tokenizer, model

    # Log the prompt
    AppendToFile(prompt + "\n...\n", f"log{main.currentFile}.txt")

    inputs = tokenizer(prompt, return_tensors="pt")

    outputs = model.generate(
        **inputs,
        max_new_tokens=120,
        do_sample=True,
        temperature=0.7
    )

    generatedTokens = outputs[0][inputs["input_ids"].shape[-1]:]

    outputDecoded = tokenizer.decode(generatedTokens, skip_special_tokens=True)

    return outputDecoded

# Chunking the text into smaller parts for better processing

def chunk_text(text, chunk_size=1200, overlap=200):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


def chunk_two_documents(doc1: str, doc2: str, chunk_size=1200, overlap=200):
    """
    Returns:
    {
        "doc1_chunks": [...],
        "doc2_chunks": [...]
    }
    """

    return {
        "doc1_chunks": chunk_text(doc1, chunk_size, overlap),
        "doc2_chunks": chunk_text(doc2, chunk_size, overlap)
    }

def process_chunk_pairs(doc1_chunks, doc2_chunks, prompt_builder):
    results = []

    max_len = max(len(doc1_chunks), len(doc2_chunks))

    for i in range(max_len):
        chunk1 = doc1_chunks[i] if i < len(doc1_chunks) else ""
        chunk2 = doc2_chunks[i] if i < len(doc2_chunks) else ""

        print(f"Processing chunk pair {i+1}/{max_len}")

        prompt = prompt_builder(chunk1, chunk2)

        try:
            output = run_llm(prompt)

            # Log prompt builder type
            if prompt_builder == build_zero_shot_prompt:
                promptType = "zero-shot"
            elif prompt_builder == build_few_shot_prompt:
                promptType = "few-shot"
            elif prompt_builder == cot_prompt:
                promptType = "cot"

            AppendToFile(f"{promptType}\n...\n", f"log{main.currentFile}.txt")

            # Log output
            AppendToFile(output + "\n...\n", f"log{main.currentFile}.txt")

            # print("output:", output[0:25])

            results.append(output)
        except Exception as e:
            print(f"Chunk pair {i} failed:", e)

    return results

def extract_kdes_from_documents(doc1, doc2, prompt_builder):
    chunks = chunk_two_documents(doc1, doc2)

    outputs = process_chunk_pairs(
        chunks["doc1_chunks"],
        chunks["doc2_chunks"],
        prompt_builder
    )

    return outputs

def mergetoString(toMergeList: list) -> str:
    return "\n".join(toMergeList)

def AppendToFile(text: str, filePath: str) -> None:
    fullPath = os.path.join(FOLDER_PATH, filePath)
    with open(fullPath, "a", encoding="utf-8") as f:
        f.write(text)