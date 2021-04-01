FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

WORKDIR /app/

COPY ./app/app/requirements.txt /app/app/requirements.txt
RUN pip install -r app/requirements.txt

COPY ./app /app
ENV PYTHONPATH=/app
