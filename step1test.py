import step1functions

# ====================
# input and vlaidation
# ====================


# ====================
# test construct zero shot prompt
# ====================
def test_construct_zero_shot_prompt():
    text = "This is a sample text to test the construction of a zero-shot prompt."
    prompt = step1functions.buildzeroshotprompt(text)
    assert "Zero-Shot Prompt" in prompt
    assert text in prompt

# ====================
# test construct one shot prompt
# ====================
def test_construct_one_shot_prompt():
    text = "This is a sample text to test the construction of a one-shot prompt."
    prompt = step1functions.one_shot_prompt(text)
    assert "One-Shot Prompt" in prompt
    assert text in prompt

# ====================
# test construct chain of thought prompt
# ====================
def test_construct_cot_prompt():
    text = "This is a sample text to test the construction of a chain of thought prompt."
    prompt = step1functions.buildcotprompt(text)
    assert "Chain of Thought Prompt" in prompt
    assert text in prompt


# ====================
# Test identification of KDE
# ====================


# ====================
# Test logging
# ====================

if __name__ == "__main__":
    test_construct_one_shot_prompt()
    print("One-shot prompt construction test passed.")
    
    test_construct_cot_prompt()
    print("Chain of thought prompt construction test passed.")
