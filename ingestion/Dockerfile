FROM python:3.9
ENV PATH /usr/src/app/bin:$PATH
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "python3", "app.py" ]