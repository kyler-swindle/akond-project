COMP 5700

Group:
akond-project

Members:
Joshua Chen jzc0289@auburn.edu
Kyler Swindle kas0183@auburn.edu

## Installation

To install the required dependencies, run:

```
pip install -r requirements.txt
```

## Running
Task 1 is step1.py
Task 2 is step2.py
Task 3 is step3.py
Task 4 is step4.py

### Step 2 usage
A helper script is provided at `step2run.bash` for running `step2.py` on two PDF inputs from the `data/` folder.

To run Step 2:

```bash
chmod +x step2run.bash
./step2run.bash cis-r1.pdf cis-r1.pdf
```

This script expects two filenames and runs:

```bash
venv/bin/python3 step2.py "data/<input_pdf_1>" "data/<input_pdf_2>"
```

## Use demo.py
from instructions

```
python3 -m venv comp5700-venv 
source comp5700-venv/bin/activate 
pip install transformers datasets evaluate accelerate torch
cd project
python3 demo.py
```

# Deliverables
## Step 1

### PROMPT.md
we put our prompts in here

### Two YAML file outputs for two documents

### Source code for six functions
Inside of the step1new.py
### Test cases for six functions


## Step 2


## Step 3


## Step 4

