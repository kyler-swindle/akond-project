from __future__ import annotations

from pathlib import Path
from typing import Iterable
import json
import subprocess
import zipfile
import os

import pandas as pd

# set this to your actual kubescape.exe path if not in PATH
kubescapeFullPath = os.environ.get("KUBESCAPE_PATH", "kubescape")
# kubescapeFullPath =  "kubescape"


NO_NAME_DIFFS = "NO DIFFERENCES IN REGARDS TO ELEMENT NAMES"
NO_REQ_DIFFS = "NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS"
NO_DIFFS_FOUND = "NO DIFFERENCES FOUND"


def load_task2_text_files(
    name_diff_file: str | Path,
    requirement_diff_file: str | Path,
) -> tuple[str, str]:
    """
    Load the two Task-2 text files.

    Returns:
        tuple(name_diff_content, requirement_diff_content)
    """
    path1 = Path(name_diff_file)
    path2 = Path(requirement_diff_file)

    for path in (path1, path2):
        if not path.exists():
            raise FileNotFoundError(f"Text file not found: {path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        if path.suffix.lower() != ".txt":
            raise ValueError(f"Expected a .txt file, got: {path}")

    return (
        path1.read_text(encoding="utf-8").strip(),
        path2.read_text(encoding="utf-8").strip(),
    )


def determine_controls_from_differences(
    name_diff_file: str | Path,
    requirement_diff_file: str | Path,
    output_file: str | Path,
) -> str:
    """
    Determine whether Task-2 reported any differences.
    If none, write 'NO DIFFERENCES FOUND'.
    Otherwise, write one valid Kubescape control ID per line.
    """
    name_text, req_text = load_task2_text_files(name_diff_file, requirement_diff_file)

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    no_name_diffs = name_text == NO_NAME_DIFFS
    no_req_diffs = req_text == NO_REQ_DIFFS

    if no_name_diffs and no_req_diffs:
        output_path.write_text(NO_DIFFS_FOUND, encoding="utf-8")
        return NO_DIFFS_FOUND

    combined = f"{name_text}\n{req_text}".lower()

    controls: set[str] = set()

    # Map to real Kubescape control IDs.
    # These are intentionally broad/manual mappings to satisfy Task-3.
    if any(word in combined for word in ["logging", "audit", "monitor"]):
        controls.add("C-0067")  # Audit logs enabled

    if any(word in combined for word in ["encryption", "tls", "certificate", "secret"]):
        controls.add("C-0066")  # Secret/etcd encryption enabled

    if any(word in combined for word in ["auth", "authentication", "authorization", "rbac", "role"]):
        controls.add("C-0088")  # RBAC enabled

    # Some helpful extras if your YAMLs start mentioning these:
    if any(word in combined for word in ["network", "ingress", "egress", "port"]):
        controls.add("C-0030")  # Ingress and Egress blocked

    if any(word in combined for word in ["credential", "password", "token"]):
        controls.add("C-0012")  # Applications credentials in configuration files

    if not controls:
        # If differences exist but no mapping matched, fall back to all controls.
        output_path.write_text(NO_DIFFS_FOUND, encoding="utf-8")
        return NO_DIFFS_FOUND

    content = "\n".join(sorted(controls))
    output_path.write_text(content, encoding="utf-8")
    return content

def execute_kubescape_scan(
    controls_file: str | Path,
    project_yamls_zip: str | Path,
    extract_dir: str | Path = "extracted_project_yamls",
) -> pd.DataFrame:
    """
    Execute Kubescape based on the controls file.

    Behavior:
    - If controls file contains 'NO DIFFERENCES FOUND', run Kubescape with all controls.
    - Otherwise, try one Kubescape control scan per listed control ID.
    - If all mapped control scans fail, fall back to a full scan.

    Returns:
        pandas DataFrame of scan summary results
    """
    controls_path = Path(controls_file)
    zip_path = Path(project_yamls_zip)
    extract_path = Path(extract_dir)

    if not controls_path.exists():
        raise FileNotFoundError(f"Controls file not found: {controls_path}")
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")

    # Check if kubescape is available
    try:
        subprocess.run([kubescapeFullPath, "version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Kubescape is not installed or not in PATH. Please install Kubescape to run scans.")
        return pd.DataFrame(columns=[
            "FilePath",
            "Severity",
            "Control name",
            "Failed resources",
            "All Resources",
            "Compliance score",
        ])

    controls_text = controls_path.read_text(encoding="utf-8").strip()

    extract_path.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_path)

    def _parse_stdout_json(stdout_text: str, scanned_path: str) -> list[dict]:
        stdout_text = stdout_text.strip()
        if not stdout_text:
            return []

        raw = json.loads(stdout_text)
        rows: list[dict] = []

        controls = (
            raw.get("summaryDetails", {})
               .get("controls", {})
        )

        for control_id, control_info in controls.items():
            resource_counters = control_info.get("ResourceCounters", {})

            passed = resource_counters.get("passedResources", 0)
            failed = resource_counters.get("failedResources", 0)
            skipped = resource_counters.get("skippedResources", 0)
            excluded = resource_counters.get("excludedResources", 0)

            all_resources = passed + failed + skipped + excluded

            rows.append({
                "FilePath": scanned_path,
                "Severity": control_info.get("severity", "NA"),
                "Control name": control_info.get("name", control_id),
                "Failed resources": failed,
                "All Resources": all_resources,
                "Compliance score": control_info.get("complianceScore", "NA"),
            })

        return rows

    def _run_full_scan() -> list[dict]:
        print("checking kubescape version")

        # Check if kubescape is available
        try:
            subprocess.run([kubescapeFullPath, "version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Kubescape is not available for full scan.")
            return []

        cmd = [
            kubescapeFullPath,
            "scan",
            str(extract_path),
            "--format",
            "json",
            "--format-version",
            "v2",
        ]

        print("Running fallback full scan:")
        print(" ".join(cmd))

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return _parse_stdout_json(result.stdout, str(extract_path))

    rows: list[dict] = []

    if controls_text == NO_DIFFS_FOUND:
        rows.extend(_run_full_scan())
    else:
        controls = [line.strip() for line in controls_text.splitlines() if line.strip()]
        successful_control_scan = False

        for control_id in controls:
            cmd = [
                kubescapeFullPath,
                "scan",
                "control",
                control_id,
                str(extract_path),
                "--format",
                "json",
                "--format-version",
                "v2",
            ]

            print(f"Running control scan for {control_id}:")
            print(" ".join(cmd))

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Control scan failed for {control_id}. Continuing. Error: {e}")
                continue

            control_rows = _parse_stdout_json(result.stdout, str(extract_path))
            if control_rows:
                rows.extend(control_rows)
                successful_control_scan = True

        if not successful_control_scan:
            print("All mapped control scans failed or returned no rows. Falling back to full scan.")
            rows.extend(_run_full_scan())

    df = pd.DataFrame(
        rows,
        columns=[
            "FilePath",
            "Severity",
            "Control name",
            "Failed resources",
            "All Resources",
            "Compliance score",
        ],
    )

    return df

def generate_scan_csv(
    scan_df: pd.DataFrame,
    output_csv: str | Path,
) -> Path:
    """
    Generate the required CSV file with these headers:
    FilePath, Severity, Control name, Failed resources, All Resources, Compliance score
    """
    required_columns = [
        "FilePath",
        "Severity",
        "Control name",
        "Failed resources",
        "All Resources",
        "Compliance score",
    ]

    missing = [col for col in required_columns if col not in scan_df.columns]
    if missing:
        raise ValueError(f"DataFrame missing required columns: {missing}")

    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scan_df.to_csv(output_path, index=False)

    return output_path

if __name__ == "__main__":
    for i in range(1, 4):
        for j in range(i, 5):
            print(f"{i} {j} ======================================")

            # step 3 running
            name_diff_file = f"outputs/name_differences{i}{j}.txt"
            requirement_diff_file = f"outputs/requirement_differences{i}{j}.txt"

            controls_output_file = f"outputs/kube/kubescape_controls{i}{j}.txt"
            csv_output_file = f"outputs/kube/kubescape_scan_results{i}{j}.csv"
            project_yamls_zip = "data/project-yamls.zip"

            controls_text = determine_controls_from_differences(
                name_diff_file=name_diff_file,
                requirement_diff_file=requirement_diff_file,
                output_file=controls_output_file,
            )

            print("Controls output text:")
            print(controls_text)
            print()

            scan_df = execute_kubescape_scan(
                controls_file=controls_output_file,
                project_yamls_zip=project_yamls_zip,
            )

            print("Kubescape scan DataFrame:")
            print(scan_df)

            csv_path = generate_scan_csv(
                scan_df=scan_df,
                output_csv=csv_output_file,
            )

            print(f"CSV written to: {csv_path}")
            print()
            print(Path(csv_output_file).read_text(encoding="utf-8"))