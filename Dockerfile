FROM python:3.6.12-alpine3.12

COPY . .

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

RUN apk update && \
    apk add bash && \
    bash && \
    apk add curl && \
    apk add nano

RUN crontab crontab

CMD ["crond", "-f"]