@echo off
cd /d "YOUR_PROJECT_FOLDER_PATH"
call venv\Scripts\activate.bat
set PYTHONPATH=backend
set HF_HOME=E:YOUR_PROJECT_FOLDER_PATH\hf_cache
set SENTENCE_TRANSFORMERS_HOME=E:YOUR_PROJECT_FOLDER_PATH\hf_cache
set TRANSFORMERS_CACHE=E:YOUR_PROJECT_FOLDER_PATH\hf_cache
uvicorn app.main:app --host 0.0.0.0 --port 8000
