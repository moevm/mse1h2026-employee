FROM python:3.11.10-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    TZ=Europe/Moscow

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tzdata \
        ca-certificates \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

WORKDIR /app

RUN pip install --no-cache-dir \
        pip==24.3.1 \
        setuptools==75.6.0 \
        wheel==0.45.1

COPY requirements.txt /app/requirements.txt
COPY docker_constraints.txt /app/docker_constraints.txt
 
RUN pip install --no-cache-dir \
        -c /app/docker_constraints.txt \
        -r /app/requirements.txt

COPY src/ /app/src/
COPY pytest.ini /app/pytest.ini

RUN groupadd --system --gid 1001 botgroup \
    && useradd --system --uid 1001 --gid botgroup --home-dir /app --shell /usr/sbin/nologin botuser \
    && chown -R botuser:botgroup /app

USER botuser

WORKDIR /app/src

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD pgrep -f "python.*main.py" > /dev/null || exit 1

CMD ["python", "main.py"]
