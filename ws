FROM python:3.9-bullseye
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /proj
WORKDIR /proj
COPY ./req.txt .
RUN pip3 install -r req.txt


COPY . /proj

CMD daphne -p 3001 mailcollector.asgi:application
# CMD python -m gunicorn mailcollector.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:3001