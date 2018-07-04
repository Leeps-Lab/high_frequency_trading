FROM python:3-alpine

ENV REDIS_URL="redis://redis:6379" \
    DJANGO_SETTINGS_MODULE="settings" \
    PIP_NO_BUILD_ISOLATION=false

ADD ./ /opt/otree

RUN apk -U add --no-cache bash \
                          curl \
                          gcc \
                          musl-dev \
                          postgresql \
                          postgresql-dev \
    && pip install --no-cache-dir -r /opt/otree/requirements.txt \
    && mkdir -p /opt/init \
    && chmod +x /opt/otree/entrypoint.sh \
    && apk del curl gcc musl-dev postgresql-dev

WORKDIR /opt/otree
VOLUME /opt/init
ENTRYPOINT /opt/otree/entrypoint.sh
EXPOSE 80
