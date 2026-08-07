ARG PYTHON_VERSION
FROM public.ecr.aws/lambda/python:${PYTHON_VERSION:-3.14}

RUN dnf install ca-certificates -y

ARG PIP_INDEX_URL

COPY requirements.txt ${LAMBDA_TASK_ROOT}/

RUN python -m venv venv && \
    source ./venv/bin/activate && \
    pip install --index-url "${PIP_INDEX_URL}" --requirement requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY src tests ${LAMBDA_TASK_ROOT}/

CMD [ "handler.lambda_handler" ]
