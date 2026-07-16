# =====================================================================
# NVIDIA DeepStream 7.x Dockerfile for AI Pipeline Service
# =====================================================================

FROM nvcr.io/nvidia/deepstream:7.0-samples-multiarch

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-dev \
    python3-gi \
    python3-gst-1.0 \
    python3-numpy \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer1.0-dev \
    libgirepository1.0-dev \
    libcairo2-dev \
    libglib2.0-dev \
    libssl-dev \
    librdkafka-dev \
    pkg-config \
    git \
    cmake \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install PyDS (NVIDIA DeepStream Python Bindings)
# NVIDIA provides pre-compiled bindings inside the container samples or we download the official release wheel.
# For DeepStream 7.0, the bindings wheel can be installed directly from the release repository.
WORKDIR /opt/nvidia/deepstream/deepstream/sources
RUN git clone https://github.com/NVIDIA-AI-IOT/deepstream_python_apps.git && \
    cd deepstream_python_apps && \
    git submodule update --init && \
    cd 3rdparty/gst-python && \
    ./autogen.sh && \
    make && \
    make install

# Compile and install pyds
WORKDIR /opt/nvidia/deepstream/deepstream/sources/deepstream_python_apps/bindings
RUN pip3 install --upgrade pip && \
    pip3 install wheel setuptools && \
    python3 setup.py bdist_wheel && \
    pip3 install dist/pyds-*.whl

# Setup app workspace
WORKDIR /app

# Copy and install Python service requirements
COPY apps/ai-service/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy monorepo packages/contracts and AI service source code
COPY apps/ai-service/src/ /app/apps/ai-service/src/
COPY apps/ai-service/configs/ /app/apps/ai-service/configs/
COPY packages/ /app/packages/

# Add python path
ENV PYTHONPATH=/app

# Run AI service
ENTRYPOINT ["python3", "/app/apps/ai-service/src/main.py"]
