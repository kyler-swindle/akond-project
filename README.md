# COMP 5700 Group Project

#### Group Name:
akond-project

#### Members:
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

#### Setting up venv
```
python3 -m venv comp5700-venv 
source comp5700-venv/bin/activate 
pip install -r requirements.txt
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
text files pairs are located in 

### Source code for the three functions
In file `step2.py`

### Test cases for the three functions. One test case for each of the three functions
In file `step2test.py`

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
Github action log located at https://github.com/kyler-swindle/akond-project/actions
github workflow file is located at `.github/workflows/run-test.yml`

### A binary that can be executed in a Python virtual environment
File `step2run.sh`

##### Instructions for `step2run.sh`
A helper script is provided at `step2run.sh` for running `step2.py` on two PDF inputs from the `/data/` folder.

##### To run Step 2:

First make it executable
```
chmod +x step2run.sh
```

This script expects two filenames and runs:

```
./step2run.sh "<input_pdf_1>" "<input_pdf_2>"
```

Example:
```
./step2run.sh cis-r1.pdf cis-r1.pdf
```

##### note: the /data/ folder will be appended automatically
##### note: run using wsl

### A `requirements.txt` file
File `requirements.txt`
