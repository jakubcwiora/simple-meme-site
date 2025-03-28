FROM python:3.12-slim

WORKDIR /app

COPY readFile.py /app/readFile.py
COPY input.md /app/input.md 

RUN pip install sympy antlr4-python3-runtime

CMD ["python", "readFile.py"]