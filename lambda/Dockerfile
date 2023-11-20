FROM public.ecr.aws/lambda/python:3.11

RUN pip install poetry

COPY pyproject.toml poetry.lock ${LAMBDA_TASK_ROOT}

RUN poetry config virtualenvs.create false

RUN poetry install

COPY app.py ${LAMBDA_TASK_ROOT}

CMD ["app.handler"]
