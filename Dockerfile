FROM mcr.microsoft.com/playwright/python:v1.33.0

# 修改时区
ENV TZ=Asia/Shanghai

WORKDIR /app
COPY . /app

# RUN apt-get update && apt-get install -y cron && apt-get install -y ffmpeg
RUN apt-get update && apt-get install -y \
  cron \
  && rm -rf /var/lib/apt/lists/*

# 创建定时任务
RUN crontab /app/crontab

# 执行定时任务
CMD ["cron","-f", "-l", "2"]

