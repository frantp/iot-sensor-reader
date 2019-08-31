FROM arm32v6/python:3-alpine

ARG sensor_flags=""

WORKDIR /sreader

RUN apk add --no-cache --virtual .glibc-deps ca-certificates wget && \
    wget -qO /etc/apk/keys/sgerrand.rsa.pub https://alpine-pkgs.sgerrand.com/sgerrand.rsa.pub && \
    wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.30-r0/glibc-2.30-r0.apk && \
    apk add libc6-compat glibc-2.30-r0.apk && \
    apk del .glibc-deps
COPY fix_deps.py requirements.txt ./
RUN apk add --no-cache --virtual .build-deps build-base linux-headers && \
    python fix_deps.py requirements.txt final_requirements.txt ${sensor_flags} && \
    pip install --no-cache-dir -r final_requirements.txt && \
    apk del .build-deps
COPY src/ src/

CMD ["python", "-u", "src/loop.py", "sreader.conf"]