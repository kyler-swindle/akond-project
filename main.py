# step 1 running
import os
import sys
from dotenv import load_dotenv

import step1

currentFile = "34"

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
        
    # only needs to be ran once
    step1.TurnAllPDFIntoText()

    # load API token
    load_dotenv()
    step1.HF_TOKEN = os.getenv("HF_TOKEN")
    
    if step1.HF_TOKEN is None:
        raise ValueError("HF_TOKEN not found in environment variables. Please set it in the .env file.")

    # load pretrained model and tokenizer
    print("Loading model and tokenizer...")
    step1.LoadModel()
    print("Model and tokenizer loaded successfully.")


    # step 1 running

    # Log model name
    step1.AppendToFile(step1.model_name + "\n...\n", f"log{currentFile}.txt")

    print("loading files")
    file1 = step1.LoadTextFromFile(f"cis-r{currentFile[0]}.txt")
    file2 = step1.LoadTextFromFile(f"cis-r{currentFile[1]}.txt")

    # print("=====files=====")
    # print(file1)
    # print("-----")
    # print(file2)
    # print("=====files=====")

    print("started extract_kdes_from_documents")
    outputs = step1.extract_kdes_from_documents(file1, file2, step1.build_zero_shot_prompt)
    # print(outputs)
    print("finish extract_kdes_from_documents")

    print("started merge_kdes")
    mergedString = step1.mergetoString(outputs)
    mergeString = mergedString.replace("/n", "\n")
    # print("mergedString:", mergedString)

    print("saving merged kdes to file")
    step1.SaveToTextFile(mergedString, f"data/merged-cis-r{currentFile}.txt")
    print("finish merge_kdes")