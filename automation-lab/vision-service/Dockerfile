FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System deps and Tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    libsm6 libxext6 libxrender-dev libgl1 libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Layer order: least-changing first -> most-changing last
# 1) torch CPU (heavy, almost never changes)
# 2) requirements.txt (changes occasionally)
# 3) EasyOCR models (depend on easyocr from step 2)
# 4) app code (changes constantly)
# Install CPU-only torch/torchvision FIRST so easyocr finds them already satisfied
# and does not download the heavy CUDA build (avoids installing torch twice).
RUN pip install --upgrade pip \
  && pip install --no-cache-dir torch==2.14.1 torchvision==0.29.1 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Bake EasyOCR models into the image (downloaded once at build, not at runtime).
# Keep EASYOCR_LANGS in sync with VisionConfig.OCR_LANGUAGES.
ARG EASYOCR_LANGS="en,es"
RUN python -c "import easyocr, os; easyocr.Reader(os.environ.get('EASYOCR_LANGS', '${EASYOCR_LANGS}').split(','), gpu=False)"

COPY . /app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

