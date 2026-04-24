import step2

def test_load_yaml_files():
    # Test with valid YAML files
    data1, data2 = step2.load_yaml_files("data/cis-r1-kdes.yaml", "data/cis-r2-kdes.yaml")
    assert isinstance(data1, dict)
    assert isinstance(data2, dict)

def test_compare_element_names():
    name_output = step2.compare_element_names(
        f"data/IndividualCleanedAgain/cis-r1-kdes.yaml",
        f"data/IndividualCleanedAgain/cis-r1-kdes.yaml",
        f"outputs/name_differences11.txt"
    )

    assert name_output is not None


def test_compare_element_names_and_requirements():
    req_output = step2.compare_element_names_and_requirements(
        f"data/IndividualCleanedAgain/cis-r1-kdes.yaml",
        f"data/IndividualCleanedAgain/cis-r1-kdes.yaml",
        f"outputs/requirement_differences11.txt"
    )

    assert req_output is not None

if __name__ == "__main__":
    test_load_yaml_files()
    print("All tests passed!")

    test_compare_element_names()
    print("compare_element_names test passed!")

    test_compare_element_names_and_requirements()
    print("compare_element_names_and_requirements test passed!")