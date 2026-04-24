from pathlib import Path
import json
import tempfile
from unittest.mock import patch

import pandas as pd

import step3

def test_load_task2_text_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = "outputs/name_differences11.txt"
        file2 = "outputs/requirement_differences11.txt"

        file1.write_text(step3.NO_NAME_DIFFS, encoding="utf-8")
        file2.write_text(step3.NO_REQ_DIFFS, encoding="utf-8")

        text1, text2 = step3.load_task2_text_files(file1, file2)

        assert text1 == step3.NO_NAME_DIFFS
        assert text2 == step3.NO_REQ_DIFFS


def test_determine_controls_from_differences():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        file1 = "outputs/name_differences11.txt"
        file2 = "outputs/requirement_differences11.txt"
        output = "test/controls.txt"

        file1.write_text("authentication", encoding="utf-8")
        file2.write_text(
            "authentication,ABSENT-IN-a.yaml,PRESENT-IN-b.yaml,REQ1",
            encoding="utf-8",
        )

        content = step3.determine_controls_from_differences(file1, file2, output)

        print(content)

        assert output.exists()
        assert "Role Based Access Control (RBAC)" in content


def test_execute_kubescape_scan():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        controls_file = "test/controls.txt"
        controls_file.write_text(step3.NO_DIFFS_FOUND, encoding="utf-8")

        zip_file = "data/project-yamls.zip"
        extract_dir = "data/extract_me"
        extract_dir.mkdir()

        sample_yaml = extract_dir / "deployment.yaml"
        sample_yaml.write_text("apiVersion: v1\nkind: Pod\n", encoding="utf-8")

        # Build a tiny zip for input.
        import zipfile
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.write(sample_yaml, arcname="deployment.yaml")

        mocked_output_json = tmp / "extracted_project_yamls" / "kubescape_results.json"
        mocked_output_json.parent.mkdir(parents=True, exist_ok=True)
        mocked_output_json.write_text(
            json.dumps({
                "frameworkReports": [
                    {
                        "controlReports": [
                            {
                                "filePath": "deployment.yaml",
                                "severity": "high",
                                "name": "Secrets management",
                                "failedResources": 1,
                                "allResources": 2,
                                "complianceScore": 50,
                            }
                        ]
                    }
                ]
            }),
            encoding="utf-8",
        )

        with patch("src.executor.subprocess.run") as mock_run:
            df = step3.execute_kubescape_scan(
                controls_file=controls_file,
                project_yamls_zip=zip_file,
            )

        mock_run.assert_called_once()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert list(df.columns) == [
            "FilePath",
            "Severity",
            "Control name",
            "Failed resources",
            "All Resources",
            "Compliance score",
        ]


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

        result = generate_scan_csv(df, output_csv)

        assert result.exists()
        content = result.read_text(encoding="utf-8")
        assert "FilePath,Severity,Control name,Failed resources,All Resources,Compliance score" in content

if __name__ == "__main__":
    test_load_task2_text_files()
    test_determine_controls_from_differences()
    test_execute_kubescape_scan()
    test_generate_scan_csv()
    print("All tests passed!")