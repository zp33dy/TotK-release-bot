FROM ubuntu:20.04
FROM python:3.10.4
RUN apt update
RUN apt upgrade -y
RUN useradd -ms /bin/bash inu
RUN usermod -aG sudo inu
WORKDIR /home/inu
USER inu
ADD requirements.txt requirements.txt
RUN pip install asyncpg matplotlib
RUN pip install -r requirements.txt
COPY . .
USER root
RUN chown -R inu: /home/inu
USER inu
WORKDIR /home/inu
CMD ["python3", "src/main.py"]