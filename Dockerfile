FROM mcr.microsoft.com/playwright/python:v1.33.0

# 修改时区
ENV TZ=Asia/Shanghai

WORKDIR /app
COPY . /app

# 安装项目依赖
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir

CMD ["python", "/app/entry.py"]

