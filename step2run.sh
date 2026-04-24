#!/bin/bash

# Usage function
usage() {
    echo "Usage: $0 <input_pdf_1> <input_pdf_2>"
    echo "Example: $0 cis-r1.pdf cis-r1.pdf"
    exit 1
}

# Check if exactly 2 arguments are provided
if [ $# -ne 2 ]; then
    echo "Error: Missing required inputs."
    usage
fi

INPUT1="data"/$1
INPUT2="data"/$2

# Optional: check if files exist
if [ ! -f "$INPUT1" ]; then
    echo "Error: File not found -> $INPUT1"
    exit 1
fi

if [ ! -f "$INPUT2" ]; then
    echo "Error: File not found -> $INPUT2"
    exit 1
fi

# Run Python script
venv/bin/python3 step2.py "$INPUT1" "$INPUT2"