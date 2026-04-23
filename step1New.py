# step 1 running
import os
import sys
from dotenv import load_dotenv
 
import step1functions

currentFile = "1"

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
        
    # only needs to be ran once
    step1functions.TurnAllPDFIntoText()

    # load API token
    load_dotenv()
    step1functions.HF_TOKEN = os.getenv("HF_TOKEN")
    
    if step1functions.HF_TOKEN is None:
        raise ValueError("HF_TOKEN not found in environment variables. Please set it in the .env file.")

    # load pretrained model and tokenizer
    print("Loading model and tokenizer...")
    step1functions.LoadModel()
    print("Model and tokenizer loaded successfully.")

    # step 1 running

    # Log model name
    # step1.AppendToFile(step1.model_name + "\n...\n", f"log{currentFile}.txt")

    print("loading files")

    print("joshua ===== joshua")

    file = step1functions.LoadTextFromFile(f"cis-r{currentFile[0]}.txt")
    prompt = step1functions.buildzeroshotprompt(file)

    print(prompt)

    print("joshua ===== joshua")

    output = step1functions.run_llm(prompt)

    print(output)

    print("joshua ===== joshua")
