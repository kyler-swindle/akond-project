import re
import yaml
import os

def extract_yaml_blocks(text: str):
    pattern = r"(element\d+:.*?)(?=\n\S|\Z)"  # grab YAML-like sections
    matches = re.findall(pattern, text, re.DOTALL)
    return matches

def parse_yaml_blocks(blocks):
    parsed = []

    for b in blocks:
        try:
            data = yaml.safe_load(b)
            if isinstance(data, dict):
                parsed.append(data)
        except:
            continue  # skip garbage

    return parsed

def clean_and_merge(parsed_list):
    merged = {}

    for data in parsed_list:
        for key, value in data.items():

            if not isinstance(value, dict):
                continue

            name = value.get("name")

            if name is None:
                name = ""
            else:
                name = str(name).strip()

            reqs = value.get("requirements", [])

            if not isinstance(reqs, list):
                reqs = [reqs]

            # clean requirements
            clean_reqs = []
            for r in reqs:
                if not r:
                    continue
                r = str(r).strip()
                if r == "" or r.lower() in ["none", "null"]:
                    continue
                clean_reqs.append(r)

            # merge
            if key not in merged:
                merged[key] = {
                    "name": name,
                    "requirements": set(clean_reqs)
                }
            else:
                merged[key]["requirements"].update(clean_reqs)

    # convert sets → lists
    for k in merged:
        merged[k]["requirements"] = list(merged[k]["requirements"])

    return merged

def save_clean_yaml(data, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False)

def clean_yaml_file(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    text = text.replace("\\n", "\n")  # fix newline issue

    blocks = extract_yaml_blocks(text)
    parsed = parse_yaml_blocks(blocks)
    cleaned = clean_and_merge(parsed)

    save_clean_yaml(cleaned, output_file)

if __name__ == "__main__":
    for i in range(1, 4):
        for j in range(i, 5):
            if os.path.exists(f"data/merged-cis-r{i}{j}.txt"):
                currentFile = f"{i}{j}"

                print(f"{currentFile}")

                clean_yaml_file(f"data/merged-cis-r{currentFile}.txt", f"data/cleanedData/merged-cis-r{currentFile}.yml")