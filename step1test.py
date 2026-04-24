import step1functions

# ====================
# input and vlaidation
# ====================
def test_pdf_to_txt():
    text = step1functions.pdf_to_txt("cis-r1.pdf")

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
    prompt = step1functions.build_zero_shot_prompt(text)
    assert "Extract Key Data Elements (KDEs) and their requirements" in prompt
    assert text in prompt

# ====================
# test construct one shot prompt
# ====================
def test_construct_few_shot_prompt():
    text = "This is a sample text to test the construction of a few-shot prompt."
    prompt = step1functions.build_few_shot_prompt(text)
    assert "Extract Key Data Elements (KDEs) and their requirements" in prompt
    assert text in prompt
    
# ====================
# test construct chain of thought prompt
# ====================
def test_construct_cot_prompt():
    text = "This is a sample text to test the construction of a chain of thought prompt."
    prompt = step1functions.build_chain_of_thought_prompt(text)
    assert "Extract Key Data Elements (KDEs) and their requirements" in prompt
    assert text in prompt


# ====================
# Test identification of KDE without loading the real LLM
# ====================
def test_identify_kde():
    text = "This is a sample text to test the identification of KDEs."
    prompt = step1functions.build_zero_shot_prompt(text)

    fake_output = """
element1:
  name: Authentication
  requirements:
    - Must identify users before access is granted
"""

    output = fake_output

    yaml_text = step1functions.extract_yaml(output)
    data = step1functions.parse_yaml(yaml_text)

    assert data is not None
    assert "element1" in data
    assert data["element1"]["name"] == "Authentication"
    assert "Must identify users before access is granted" in data["element1"]["requirements"]
    assert "Extract Key Data Elements" in prompt

# ====================
# Test logging helper
# ====================
def test_write_llm_output_log():
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "task1_llm_output.txt"

        result = step1functions.write_llm_output_log(
            output_file=output_file,
            llm_name="google/gemma-3-1b-it",
            prompt_type="zero-shot",
            prompt_used="Identify KDEs from this document.",
            llm_output="element1:\n  name: Authentication\n  requirements:\n    - Must authenticate users",
        )

        assert result.exists()

        content = result.read_text(encoding="utf-8")
        assert "*LLM Name*" in content
        assert "google/gemma-3-1b-it" in content
        assert "*Prompt Used*" in content
        assert "Identify KDEs from this document." in content
        assert "*Prompt Type*" in content
        assert "zero-shot" in content
        assert "*LLM Output*" in content
        assert "Authentication" in content


# ====================
# Test process_file without loading the real LLM
# ====================
def test_process_file_with_mocked_llm():
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "cis-r-test.txt"
        input_file.write_text("The system must use authentication.", encoding="utf-8")

        fake_output = """
element1:
  name: Authentication
  requirements:
    - The system must use authentication.
"""

        original_run_llm = step1functions.run_llm

        try:
            step1functions.run_llm = lambda prompt, tokenizer, model: fake_output

            result = step1functions.process_file(
                file_path=input_file,
                tokenizer=None,
                model=None,
                prompt_builder=step1functions.build_zero_shot_prompt,
                prompt_type="zero-shot",
            )

            assert "authentication" in result
            assert result["authentication"]["name"] == "Authentication"
            assert "The system must use authentication." in result["authentication"]["requirements"]

            log_file = Path(tmpdir) / "cis-r-test-zero-shot-llm-output.txt"
            assert log_file.exists()

            log_text = log_file.read_text(encoding="utf-8")
            assert "*LLM Name*" in log_text
            assert "google/gemma-3-1b-it" in log_text
            assert "*Prompt Used*" in log_text
            assert "*Prompt Type*" in log_text
            assert "zero-shot" in log_text
            assert "*LLM Output*" in log_text

        finally:
            step1functions.run_llm = original_run_llm

# ====================
# Test logging
# ====================

if __name__ == "__main__":
    test_pdf_to_txt()
    print("PDF to text conversion test passed.")

    test_construct_zero_shot_prompt()
    print("Zero-shot prompt construction test passed.")

    test_construct_few_shot_prompt()
    print("Few-shot prompt construction test passed.")

    test_construct_cot_prompt()
    print("Chain of thought prompt construction test passed.")

    test_identify_kde()
    print("KDE identification test passed.")

    test_write_llm_output_log()
    print("LLM output logging test passed.")

    test_process_file_with_mocked_llm()
    print("Mocked process_file test passed.")