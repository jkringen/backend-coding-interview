FROM python:3.12-slim
RUN apt-get update -y && apt-get install -y --no-install-recommends build-essential libxml2-dev gcc libpq-dev curl netcat-openbsd procps
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:${PATH}"
WORKDIR /code
COPY poetry.lock pyproject.toml /code/
RUN poetry install --only main
COPY . /code
RUN poetry run python manage.py collectstatic --noinput