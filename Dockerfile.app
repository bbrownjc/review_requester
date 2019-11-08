FROM python:3.7.5
ENV PYTHONDONTWRITEBYTECODE=1

COPY . /opt/src
WORKDIR /opt/src
RUN pip install poetry && poetry config settings.virtualenvs.create false && poetry install

RUN apt-get update && \
    apt-get install -y sudo && \
    rm -rf /var/lib/apt/lists/*
RUN useradd --user-group --system --create-home --no-log-init postgres
USER postgres


ENV FLASK_APP=app.py
# RUN python -c "from app import db; db.create_all()"
CMD flask run --host=0.0.0.0
