from pathlib import Path
import json
import tempfile
from unittest.mock import Mock, patch
import zipfile

import pandas as pd

import step3


def test_load_task2_text_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        file1 = tmp / "name_differences11.txt"
        file2 = tmp / "requirement_differences11.txt"

        file1.write_text(step3.NO_NAME_DIFFS, encoding="utf-8")
        file2.write_text(step3.NO_REQ_DIFFS, encoding="utf-8")

        text1, text2 = step3.load_task2_text_files(file1, file2)

        assert text1 == step3.NO_NAME_DIFFS
        assert text2 == step3.NO_REQ_DIFFS


def test_determine_controls_from_differences():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        file1 = tmp / "name_differences11.txt"
        file2 = tmp / "requirement_differences11.txt"
        output = tmp / "controls.txt"

        file1.write_text("authentication", encoding="utf-8")
        file2.write_text(
            "authentication,ABSENT-IN-a.yaml,PRESENT-IN-b.yaml,REQ1",
            encoding="utf-8",
        )

        content = step3.determine_controls_from_differences(file1, file2, output)

        assert output.exists()
        assert "C-0088" in content


def test_execute_kubescape_scan():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        controls_file = tmp / "controls.txt"
        controls_file.write_text(step3.NO_DIFFS_FOUND, encoding="utf-8")

        source_dir = tmp / "project_yamls"
        source_dir.mkdir()

        sample_yaml = source_dir / "deployment.yaml"
        sample_yaml.write_text("apiVersion: v1\nkind: Pod\n", encoding="utf-8")

        zip_file = tmp / "project-yamls.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.write(sample_yaml, arcname="deployment.yaml")

        extract_dir = tmp / "extracted_project_yamls"

        kubescape_json = {
            "summaryDetails": {
                "controls": {
                    "C-0012": {
                        "severity": "high",
                        "name": "Secrets management",
                        "ResourceCounters": {
                            "passedResources": 1,
                            "failedResources": 1,
                            "skippedResources": 0,
                            "excludedResources": 0,
                        },
                        "complianceScore": 50,
                    }
                }
            }
        }

        def fake_subprocess_run(cmd, capture_output=True, text=False, check=False):
            # First call is: kubescape version
            if "version" in cmd:
                return Mock(stdout="", returncode=0)

            # Second call is the actual scan.
            return Mock(stdout=json.dumps(kubescape_json), returncode=0)

        with patch("step3.subprocess.run", side_effect=fake_subprocess_run) as mock_run:
            df = step3.execute_kubescape_scan(
                controls_file=controls_file,
                project_yamls_zip=zip_file,
                extract_dir=extract_dir,
            )

        assert mock_run.call_count >= 2
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

        row = df.iloc[0]
        assert row["Severity"] == "high"
        assert row["Control name"] == "Secrets management"
        assert row["Failed resources"] == 1
        assert row["All Resources"] == 2
        assert row["Compliance score"] == 50


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
        assert "deployment.yaml,high,Secrets management,1,2,50" in content


if __name__ == "__main__":
    test_load_task2_text_files()
    test_determine_controls_from_differences()
    test_execute_kubescape_scan()
    test_generate_scan_csv()
    print("All tests passed!")