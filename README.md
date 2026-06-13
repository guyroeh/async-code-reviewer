# Automatic Code Review Platform

AI-powered Python code reviewer using a local Ollama LLM.

## Overview

This project is a Proof of Concept (POC) for an automatic code review platform.

The platform receives one Python file at a time, reviews the code using a local LLM through Ollama, and returns whether the uploaded code follows predefined review rules.

The current POC checks the following rules:

The variables in the file have meaningful names.
The function docstring matches the actual function logic.

The system runs locally and does not use cloud services.

## Technologies Used
FastAPI
Uvicorn
SQLModel
SQLite
Ollama
Requests

## Prerequisites
-Python 3.10 or newer
Ollama installed locally
Git

## Ollama Setup

Install Ollama from:

https://ollama.com

Verify that Ollama is installed:

ollama --version

Download the local model used by the project:

ollama pull llama3.2

Verify that Ollama is running locally:

curl http://localhost:11434

By default, the application expects Ollama to be available at:

http://localhost:11434/api/generate

## Python Setup

Clone this repository:

git clone <repository-url>
cd <repository-folder>

Create a virtual environment:

python -m venv venv

Activate the virtual environment.

On Windows PowerShell:

.\venv\Scripts\Activate.ps1

On macOS/Linux:

source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

## Running the Application

From the project root, run:

uvicorn app.main:app --reload

The interactive FastAPI documentation will be available at:

http://127.0.0.1:8000/docs

Use the /docs page to upload files and fetch results.

Note: opening only http://127.0.0.1:8000 may return {"detail":"Not Found"} because the project does not currently define a root endpoint.

## Usage

Open the following URL in your browser:

http://127.0.0.1:8000/docs

### Upload a Python File for Review
Open the /scan endpoint.
Click Try it out.
Upload a .py file.
Click Execute.
If the request succeeds, the response status code will be 202.
Copy the returned scan_id.

Example response:

{
  "scan_id": "b7df6cd2-2da1-46f5-8c3d-3ef12ccba951",
  "status": "PENDING"
}

### Check the Review Results

#### Result fetch by scan_id 
Open the /results/{scan_id} endpoint.
Click Try it out.
Paste the scan_id from the upload response.
Click Execute.
Read the result in the response body.

Example completed response:

{
  "scan_id": "b7df6cd2-2da1-46f5-8c3d-3ef12ccba951",
  "status": "COMPLETED",
  "results": {
    "All variables have meaningful names": true,
    "Docstring of function reflects the actual code's logic": true
  }
}
#### Result fetch by file's name
Open the /results/file/{filename} endpoint.
Click Try it out.
Paste the file's name from the upload response.
Click Execute.
Read the result in the response body.

Example completed response:

{
  "scan_id": "b7df6cd2-2da1-46f5-8c3d-3ef12ccba951",
  "status": "COMPLETED",
  "results": {
    "All variables have meaningful names": true,
    "Docstring of function reflects the actual code's logic": true
  }
}

## Test 
For testing run in the terminal the following command: pytest -v tests/

## The AI conversation: 
https://gemini.google.com/share/b170cff06879