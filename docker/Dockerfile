FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y sqlite3 libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*

#COPY requirements.txt requirements.txt
RUN  pip install --upgrade pip
RUN  pip install jwt
RUN  pip install requests
RUN  pip install Flask
RUN  pip install jsonify


#RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "App.py"]