import os
import sys
from dotenv import load_dotenv

import step1

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
    print(step1.run_llm("who are you"))
    print("Model and tokenizer loaded successfully.")

    print("loading files and building prompt")
    r1File = step1.LoadTextFromFile("cis-r1.txt")
    r2File = step1.LoadTextFromFile("cis-r2.txt")
    # prompt = step1.build_zero_shot_prompt(r1File, r2File)
    print("prompt built successfully")

    for i in range(1, 4):
        for j in range(i, 5):
            print(f"{i} {j} ======================================")
            # step 1 running

            print("started extract_kdes_from_documents")
            outputs = step1.extract_kdes_from_documents(r1File, r2File, step1.build_zero_shot_prompt)
            print("finish extract_kdes_from_documents")

            print("started merge_kdes")
            mergedDict = step1.merge_kdes(outputs)
            mergedString = step1.merged_to_yaml_string(mergedDict)

            print("saving merged kdes to file")
            step1.SaveToTextFile(mergedString, "data/merged_kdes12.txt")
            print("finish merge_kdes")


    # print("started run_llm")
    # output = step1.run_llm(prompt)
    # print("finish run_llm")
    # print(output)