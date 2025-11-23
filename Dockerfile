FROM python:3.12-slim
ENV DEBIAN_FRONTEND=noninteractive
ENV ENV=prod
ENV TZ="America/Chicago"
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app
COPY pyproject.toml /app
COPY play_outside/__about__.py /app/play_outside/__about__.py
COPY README.md /app
RUN pip3 install --no-cache-dir --root-user-action=ignore --upgrade pip
RUN pip3 install --no-cache-dir --root-user-action=ignore .
COPY . /app
RUN pip3 install --no-cache-dir --root-user-action=ignore .

EXPOSE 8100

ENTRYPOINT play-outside run --env prod
