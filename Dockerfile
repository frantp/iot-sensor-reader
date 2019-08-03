FROM python:3

WORKDIR /sreader

ARG sensor_flags="ALL"

COPY fix_deps.py requirements.txt ./
RUN python fix_deps.py requirements.txt final_requirements.txt ${sensor_flags}
RUN pip install --no-cache-dir -r final_requirements.txt

COPY src/ src/

CMD ["python", "-u", "src/loop.py"]