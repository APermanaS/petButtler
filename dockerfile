FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Memberi tahu sistem bahwa file utama aplikasinya bernama app.py
ENV FLASK_APP=app.py

# Menjalankan server Flask bawaan agar terus standby/listening
CMD ["flask", "run", "--host=0.0.0.0"]