# Linux/Mac Running Guide

This guide will help you set up and run the project step by step on a Linux/Mac environment.

# 1. Create a Virtual Environment

First, create a Python virtual environment in the project directory:

```bash
python -m venv .venv
```

# 2. Activate the Virtual Environment and Install Dependencies

Activate your virtual environment:

```bash
source ./.venv/bin/activate
```

Then install all required packages:

```bash
pip install -r requirements.txt
```

# 3. Run the Program

Finally, start the program:

```bash
python -m thu_learn_downloader.main
```
