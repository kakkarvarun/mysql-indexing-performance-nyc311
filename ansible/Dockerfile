FROM python:3.11-slim

# Ansible + Docker SDK + MySQL client for quick checks
RUN pip install --no-cache-dir ansible docker \
 && apt-get update \
 && apt-get install -y --no-install-recommends default-mysql-client curl \
 && rm -rf /var/lib/apt/lists/*

# Ansible docker collection (for docker_* modules)
RUN ansible-galaxy collection install community.docker

WORKDIR /work
