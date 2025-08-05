FROM python:3.9-slim

WORKDIR /app

RUN pip install scapy requests

COPY dns_server.py /app
COPY adservers.txt /app
COPY statistics.json /app
COPY stats.txt /app

EXPOSE 53/tcp
EXPOSE 53/udp

CMD ["python", "/app/dns_server.py"]
