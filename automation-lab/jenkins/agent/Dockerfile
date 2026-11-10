FROM mcr.microsoft.com/playwright/python:v1.62.0-noble

RUN apt-get update && apt-get install -y --no-install-recommends \
      openjdk-21-jre-headless \
      socat \
      curl \
      python3-venv \
      libgl1 \
      libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create isolated virtualenv to comply with PEP 668 on Ubuntu 24.04 (noble)
# Browser binaries remain accessible in /ms-playwright
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
 && python -c "import cv2, playwright, pytest; print('Playwright + OpenCV + Pytest OK')"

COPY automation-lab/jenkins/agent/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /workspace/automation-playwright
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

