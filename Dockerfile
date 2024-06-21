FROM ubuntu:noble
FROM python:3.10.4
# Install pip
RUN python -m ensurepip

# Upgrade pip to the latest version
RUN python -m pip install --upgrade pip

RUN useradd -ms /bin/bash inu

# Create and set permissions for /home/inu/app directory
USER inu
WORKDIR /home/inu

# Copy requirements and install dependencies
ADD requirements.txt requirements.txt
RUN pip install asyncpg matplotlib
RUN pip install -r requirements.txt

# Copy application files
COPY src src
COPY config.yaml .

USER root
# Create log directory and set permissions
RUN mkdir -p inu \
    && chown -R inu:inu inu
USER inu

CMD ["python3", "-O", "src/main.py"]
