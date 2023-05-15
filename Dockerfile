FROM mcr.microsoft.com/playwright/python:v1.33.0

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata && \
    rm -rf /var/lib/apt/lists/*

ENV DEBIAN_FRONTEND=dialog

WORKDIR /app
COPY . /app

# 安装项目依赖
RUN pip install -r requirements.txt --no-cache-dir

CMD ["python", "/app/entry.py"]

