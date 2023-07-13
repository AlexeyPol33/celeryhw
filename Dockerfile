FROM python:3.10.11

RUN apt-get update \
    && apt-get install -y libgl1-mesa-glx

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY EDSR_x2.pb .

ENV DB_HOST=db

EXPOSE 5000

CMD ["python", "app.py"]