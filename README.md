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

## Use demo.py
from instructions

```
python3 -m venv comp5700-venv 
source comp5700-venv/bin/activate 
pip install transformers datasets evaluate accelerate torch
cd project
python3 demo.py
```
---

# Deliverables


## <u>Step 1</u>

### PROMPT.md
we put our prompts in here

### Two YAML file outputs for two documents
stored in `/data/IndividualCleanedAgain/`

### Source code for six functions
Inside of the `step1new.py`

### Test cases for six functions
Located in `step1test.py`

---

## <u>Step 2</u>

### Two TEXT files as output


### Source code for the three functions

### Test cases for the three functions. One test case for each of the three functions

---

## <u>Step 3</u>

###  A CSV file
Files are located in `/outputs/kube/*.csv`

### Source code for the four functions
In file `step3.py`

### Test cases for the four functions. One test case for each of the four functions
In file `step3test.py`

## Step 4

### A public repository on github.com
https://github.com/kyler-swindle/akond-project

### A GitHub Action file with logs of test case execution


### A binary that can be executed in a Python virtual environment
File `step2run.bash`

##### Instructions for `step2run.bash`
A helper script is provided at `step2run.bash` for running `step2.py` on two PDF inputs from the `/data/` folder.

##### To run Step 2:

```bash
chmod +x step2run.bash
./step2run.bash cis-r1.pdf cis-r1.pdf
```

This script expects two filenames and runs:

```bash
./step2run.bash "<input_pdf_1>" "<input_pdf_2>"
```
##### note: the /data/ folder will be appended automatically
##### note: run using wsl

### A `requirements.txt` file
File `requirements.txt`
