FROM python:3.7.5
ENV PYTHONDONTWRITEBYTECODE=1

COPY . .
RUN pip install poetry && poetry config settings.virtualenvs.create false && poetry install

ENV FLASK_APP=app.py
# RUN python -c "from app import db; db.create_all()"
CMD flask run
