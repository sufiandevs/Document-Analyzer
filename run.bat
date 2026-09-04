@echo off
cd /d "E:\Deepvision.ai\Production-Ready Multi-Agent RAG System"
call venv\Scripts\activate.bat
set PYTHONPATH=backend
set HF_HOME=E:\Deepvision.ai\Production-Ready Multi-Agent RAG System\hf_cache
set SENTENCE_TRANSFORMERS_HOME=E:\Deepvision.ai\Production-Ready Multi-Agent RAG System\hf_cache
set TRANSFORMERS_CACHE=E:\Deepvision.ai\Production-Ready Multi-Agent RAG System\hf_cache
uvicorn app.main:app --host 0.0.0.0 --port 8000