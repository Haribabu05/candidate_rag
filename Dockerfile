FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

COPY data/ ./data

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]

#aldkj;aldkf
#idsjalsjkdl