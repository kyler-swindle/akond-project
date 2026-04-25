import step1

# ====================
# input and vlaidation
# ====================
def test_pdf_to_txt():
    text = step1.pdf_to_txt("cis-r1.pdf")

    assert text.strip() != ""
    
    textFileContent = ""

    with open("data/cis-r1.txt", "r", encoding="utf-8") as f:
        textFileContent += f.read()
    
    assert textFileContent.strip() != ""

# ====================
# test construct zero shot prompt
# ====================
def test_construct_zero_shot_prompt():
    text = "This is a sample text to test the construction of a zero-shot prompt."
    prompt = step1.build_zero_shot_prompt(text)
    assert "Extract Key Data Elements (KDEs) and their requirements" in prompt
    assert text in prompt

# ====================
# test construct one shot prompt
# ====================
def test_construct_one_shot_prompt():
    text = "This is a sample text to test the construction of a one-shot prompt."
    prompt = step1.build_one_shot_prompt(text)
    assert "Extract Key Data Elements (KDEs) and their requirements" in prompt
    assert text in prompt

# ====================
# test construct chain of thought prompt
# ====================
def test_construct_cot_prompt():
    text = "This is a sample text to test the construction of a chain of thought prompt."
    prompt = step1.build_chain_of_thought_prompt(text)
    assert "Extract Key Data Elements (KDEs) and their requirements" in prompt
    assert text in prompt


# ====================
# Test identification of KDE
# ====================
def test_identify_kde():
    tokenizer, model = step1.load_model()

    text = ""

    # read from 5000 chars of a file to test
    with open("data/cis-r1.txt", "r", encoding="utf-8") as f:
        text = f.read(5000)

    prompt = step1.build_zero_shot_prompt(text)
    output = step1.run_llm(prompt=prompt, tokenizer=tokenizer, model=model)

    assert output.strip() is not None

# ====================
# Test logging
# ====================

if __name__ == "__main__":
    test_pdf_to_txt()
    print("PDF to text conversion test passed.")

    test_construct_zero_shot_prompt()
    print("Zero-shot prompt construction test passed.")

    test_construct_one_shot_prompt()
    print("One-shot prompt construction test passed.")

    test_construct_cot_prompt()
    print("Chain of thought prompt construction test passed.")

    test_identify_kde()
    print("KDE identification test passed.")