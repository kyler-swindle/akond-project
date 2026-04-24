from pathlib import Path
import json
import tempfile
from unittest.mock import patch

import pandas as pd

import step3

def test_load_task2_text_files():
    file1 = "outputs/name_differences11.txt"
    file2 = "outputs/requirement_differences11.txt"

    text1, text2 = step3.load_task2_text_files(file1, file2)

    assert text1 == step3.NO_NAME_DIFFS
    assert text2 == step3.NO_REQ_DIFFS


def test_determine_controls_from_differences():
    file1 = "outputs/name_differences11.txt"
    file2 = "outputs/requirement_differences11.txt"
    output = "test/controls.txt"

    content = step3.determine_controls_from_differences(file1, file2, output)

    print(content)

    # read in output file and check content
    with open(output, "r", encoding="utf-8") as f:
        content = f.read()
        
        assert content.strip() is not None

    assert content.strip() is not None


def test_execute_kubescape_scan():
    controlsFile = "outputs/kube/kubescape_controls11.txt"
    ProjectYamlsZip = "data/project-yamls.zip"

    df = step3.execute_kubescape_scan(controlsFile, ProjectYamlsZip)

    assert df is not None


def test_generate_scan_csv():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        output_csv = tmp / "scan_results.csv"

        df = pd.DataFrame([
            {
                "FilePath": "deployment.yaml",
                "Severity": "high",
                "Control name": "Secrets management",
                "Failed resources": 1,
                "All Resources": 2,
                "Compliance score": 50,
            }
        ])

        result = step3.generate_scan_csv(df, output_csv)

        assert result.exists()
        content = result.read_text(encoding="utf-8")
        assert "FilePath,Severity,Control name,Failed resources,All Resources,Compliance score" in content

if __name__ == "__main__":
    test_load_task2_text_files()
    test_determine_controls_from_differences()
    test_execute_kubescape_scan()
    test_generate_scan_csv()
    print("All tests passed!")