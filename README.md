Verify installation

```bash
uv venv
uv pip install -r requirements.txt

mac/linux source .venv/bin/activate
win cmd .venv\Scripts\activate
win powershell .venv\Scripts\Activate.ps1

mac/linux uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
win .venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
python -c "import langchain_openai; print('✅ LangChain OpenAI installed')"
python -c "import langchain_huggingface; print('✅ LangChain HuggingFace installed')"
python -c "import sentence_transformers; print('✅ Sentence Transformers installed')"
python -c "import numpy; print(f'✅ NumPy {numpy.__version__}')"
```
