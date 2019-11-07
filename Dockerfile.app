FROM python:3.7.5
ENV PYTHONDONTWRITEBYTECODE=1

COPY . .
RUN pip install poetry && poetry config settings.virtualenvs.create false && poetry install
RUN pip install psycopg2

RUN apt-get update 
RUN apt-get install -y sudo && rm -rf /var/lib/apt/lists/*
RUN useradd --user-group --system --create-home --no-log-init postgres
USER postgres


ENV FLASK_APP=app.py
# RUN python -c "from app import db; db.create_all()"
CMD flask run
