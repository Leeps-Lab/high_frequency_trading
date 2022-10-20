FROM python:3.6-bullseye

COPY ./ /hft

WORKDIR /hft

RUN apt-get update -y && apt-get install -y \
    python3-pip \
    python-dev \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip setuptools wheel

RUN pip install -r requirements_base.txt
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1

RUN chmod +x /hft/bin/entrypoint.sh

ENTRYPOINT [ "/hft/bin/entrypoint.sh" ]
