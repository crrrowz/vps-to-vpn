FROM python:3.11-alpine

# Install OpenSSH client and bash
RUN apk add --no-cache openssh-client bash

WORKDIR /app

COPY deploy_tunnel.py /app/deploy_tunnel.py
COPY vps_tunnel.py /app/vps_tunnel.py

ENTRYPOINT ["python", "/app/deploy_tunnel.py"]
