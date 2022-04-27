FROM python:3.10

COPY . .
RUN python -m pip install --upgrade pip poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev

EXPOSE 8000
CMD gunicorn --bind 0.0.0.0:8000 football:server
