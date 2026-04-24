from __future__ import annotations

from pathlib import Path
import sys
from typing import Any
import yaml


def load_yaml_files(file1: str | Path, file2: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Load two YAML files produced by Task-1.

    Input validation performed:
    - path exists
    - path is a file
    - YAML parses to a dictionary

    Returns:
        tuple of parsed YAML dictionaries
    """
    path1 = Path(file1)
    path2 = Path(file2)

    for path in (path1, path2):
        if not path.exists():
            raise FileNotFoundError(f"YAML file not found: {path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        if path.suffix.lower() not in {".yaml", ".yml"}:
            raise ValueError(f"Expected a YAML file, got: {path}")

    with path1.open("r", encoding="utf-8") as f1:
        data1 = yaml.safe_load(f1)

    with path2.open("r", encoding="utf-8") as f2:
        data2 = yaml.safe_load(f2)

    if not isinstance(data1, dict):
        raise ValueError(f"YAML root must be a dictionary in file: {path1}")
    if not isinstance(data2, dict):
        raise ValueError(f"YAML root must be a dictionary in file: {path2}")

    return data1, data2


def _normalize_name(value: str) -> str:
    return value.strip().lower()


def _normalize_requirement(value: str) -> str:
    return value.strip().lower()


def _extract_name_to_requirements(data: dict[str, Any]) -> dict[str, set[str]]:
    """
    Convert Task-1 YAML into a normalized mapping:
        KDE name -> set(requirements)

    Expected per-element structure:
    element1:
      name: ...
      requirements:
        - req1
        - req2
    """
    result: dict[str, set[str]] = {}

    for element_key, element_value in data.items():
        if not isinstance(element_value, dict):
            raise ValueError(f"Element '{element_key}' must map to a dictionary.")

        raw_name = element_value.get("name")
        raw_requirements = element_value.get("requirements", [])

        if not isinstance(raw_name, str) or not raw_name.strip():
            raise ValueError(f"Element '{element_key}' is missing a valid 'name' field.")

        if not isinstance(raw_requirements, list):
            raise ValueError(f"Element '{element_key}' has non-list 'requirements' field.")

        normalized_name = _normalize_name(raw_name)

        normalized_requirements: set[str] = set()
        for req in raw_requirements:
            if not isinstance(req, str) or not req.strip():
                continue  # Skip invalid requirement entries
            normalized_requirements.add(_normalize_requirement(req))

        result[normalized_name] = normalized_requirements

    return result


def compare_element_names(
    file1: str | Path,
    file2: str | Path,
    output_file: str | Path,
) -> str:
    """
    Identify differences in KDE names across two YAML files.

    Output format:
    - one differing name per line
    - or 'NO DIFFERENCES IN REGARDS TO ELEMENT NAMES'
    """
    data1, data2 = load_yaml_files(file1, file2)
    names1 = set(_extract_name_to_requirements(data1).keys())
    names2 = set(_extract_name_to_requirements(data2).keys())

    differing_names = sorted(names1.symmetric_difference(names2))

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not differing_names:
        content = "NO DIFFERENCES IN REGARDS TO ELEMENT NAMES"
    else:
        content = "\n".join(differing_names)

    output_path.write_text(content, encoding="utf-8")
    return content


def compare_element_names_and_requirements(
    file1: str | Path,
    file2: str | Path,
    output_file: str | Path,
) -> str:
    """
    Identify differences in KDE names and requirements.

    Required output tuple format:
    NAME,ABSENT-IN-<FILENAME>,PRESENT-IN-<FILENAME>,NA
    NAME,ABSENT-IN-<FILENAME>,PRESENT-IN-<FILENAME>,REQ1

    Rules:
    - If a KDE exists in one file but not the other, emit one line with NA
    - If a KDE exists in both files but has differing requirements,
      emit one line per missing requirement
    - If no differences, emit:
      'NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS'
    """
    data1, data2 = load_yaml_files(file1, file2)
    map1 = _extract_name_to_requirements(data1)
    map2 = _extract_name_to_requirements(data2)

    file1_name = Path(file1).name
    file2_name = Path(file2).name

    lines: list[str] = []

    names1 = set(map1.keys())
    names2 = set(map2.keys())

    only_in_1 = sorted(names1 - names2)
    only_in_2 = sorted(names2 - names1)

    for name in only_in_1:
        lines.append(f"{name},ABSENT-IN-{file2_name},PRESENT-IN-{file1_name},NA")

    for name in only_in_2:
        lines.append(f"{name},ABSENT-IN-{file1_name},PRESENT-IN-{file2_name},NA")

    for name in sorted(names1.intersection(names2)):
        reqs1 = map1[name]
        reqs2 = map2[name]

        missing_from_2 = sorted(reqs1 - reqs2)
        missing_from_1 = sorted(reqs2 - reqs1)

        for req in missing_from_2:
            lines.append(f"{name},ABSENT-IN-{file2_name},PRESENT-IN-{file1_name},{req}")

        for req in missing_from_1:
            lines.append(f"{name},ABSENT-IN-{file1_name},PRESENT-IN-{file2_name},{req}")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not lines:
        content = "NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS"
    else:
        content = "\n".join(lines)

    output_path.write_text(content, encoding="utf-8")
    return content

# new run to work with bash file
if __name__ == "__main__":
    print(sys.argv)

    (i, j) = (sys.argv[1][10], sys.argv[2][10])
    print(f"{i} {j} ======================================")

    # step 2 running
    Path("outputs").mkdir(exist_ok=True)

    name_output = compare_element_names(
        f"data/IndividualCleanedAgain/cis-r{i}-kdes.yaml",
        f"data/IndividualCleanedAgain/cis-r{j}-kdes.yaml",
        f"outputs/name_differences{i}{j}.txt"
    )

    req_output = compare_element_names_and_requirements(
        f"data/IndividualCleanedAgain/cis-r{i}-kdes.yaml",
        f"data/IndividualCleanedAgain/cis-r{j}-kdes.yaml",
        f"outputs/requirement_differences{i}{j}.txt"
    )

    print("Names output:")
    print(name_output)
    print()
    print("Requirements output:")
    print(req_output)

# if __name__ == "__main__":
#     """
#     run cell
#     """

#     for i in range(1, 4):
#         for j in range(i, 5):
#             print(f"{i} {j} ======================================")
#             # step 2 running

#             Path("outputs").mkdir(exist_ok=True)

#             name_output = compare_element_names(
#                 f"data/IndividualCleanedAgain/cis-r{i}-kdes.yaml",
#                 f"data/IndividualCleanedAgain/cis-r{j}-kdes.yaml",
#                 f"outputs/name_differences{i}{j}.txt"
#             )

#             req_output = compare_element_names_and_requirements(
#                 f"data/IndividualCleanedAgain/cis-r{i}-kdes.yaml",
#                 f"data/IndividualCleanedAgain/cis-r{j}-kdes.yaml",
#                 f"outputs/requirement_differences{i}{j}.txt"
#             )

#             print("Names output:")
#             print(name_output)
#             print()
#             print("Requirements output:")
#             print(req_output)