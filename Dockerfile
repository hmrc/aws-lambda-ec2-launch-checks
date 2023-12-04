FROM public.ecr.aws/lambda/python:3.9

RUN yum install ca-certificates -y

COPY requirements.txt requirements-tests.txt setup.cfg ${LAMBDA_TASK_ROOT}/

RUN PIP_INDEX_URL=https://artefacts.tax.service.gov.uk/artifactory/api/pypi/pips/simple \
    python -m venv venv && \
    source ./venv/bin/activate && \
    pip install --upgrade pip && \
    pip install --requirement requirements-tests.txt --target "${LAMBDA_TASK_ROOT}"

COPY src tests ${LAMBDA_TASK_ROOT}/

CMD [ "handler.lambda_handler" ]
