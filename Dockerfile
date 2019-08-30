FROM arm32v6/python:3-alpine

ARG sensor_flags=""

WORKDIR /sreader

COPY fix_deps.py requirements.txt ./
RUN apk add --no-cache --virtual .build-deps build-base linux-headers && \
    python fix_deps.py requirements.txt final_requirements.txt ${sensor_flags} && \
    pip install --no-cache-dir -r final_requirements.txt && \
    apk del .build-deps
COPY src/ src/

CMD ["python", "-u", "src/loop.py", "sreader.conf"]