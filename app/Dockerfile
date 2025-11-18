# Multi-stage Dockerfile for KATH Genetic Analysis Tool
# Stage 1: Build large reference files
FROM python:3.12-alpine3.20 AS files

RUN apk add --no-cache curl unzip

# Download hg38.fa.gz file needed for SpliceAI
RUN curl "https://hgdownload.cse.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz" | gunzip -c > /hg38.fa

# Download hg19ToHg38.over.chain.gz file needed for pyliftover
RUN curl -O "http://hgdownload2.cse.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz"

COPY --link ./back_end/src/scripts/revel.py /revel.py

# Download and convert REVEL database
RUN curl -O "https://rothsj06.dmz.hpc.mssm.edu/revel-v1.3_all_chromosomes.zip" && \
    unzip revel-v1.3_all_chromosomes.zip && \
    pip install --no-cache-dir --root-user-action ignore -t /delete tqdm && \
    PYTHONPATH=/delete python3 /revel.py revel_with_transcript_ids /revel_with_transcript_ids.db && \
    rm -rf revel-v1.3_all_chromosomes.zip /revel_with_transcript_ids /delete

# Stage 2: Final application image
FROM nvidia/cuda:12.9.1-base-ubuntu24.04

# Copy reference files from build stage
COPY --chmod=644 --link --from=files /hg38.fa /reference_files/
COPY --chmod=644 --link --from=files /revel_with_transcript_ids.db /reference_files/
COPY --chmod=644 --link --from=files /hg19ToHg38.over.chain.gz /root/.pyliftover/

# Install system dependencies
# Note: Install from Mozilla's PPA for proper Firefox binary (not snap)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.12 \
        python3-pip \
        redis-server \
        wget \
        curl \
        ca-certificates \
        git \
        bzip2 \
        && \
    rm -rf /var/lib/apt/lists/*

# Install Firefox from official Mozilla binary (not snap wrapper)
# Use a known stable Firefox ESR version from Mozilla FTP
RUN mkdir -p /opt && \
    wget --quiet "https://ftp.mozilla.org/pub/firefox/releases/128.0esr/linux-x86_64/en-US/firefox-128.0esr.tar.bz2" -O /tmp/firefox.tar.bz2 && \
    tar -xjf /tmp/firefox.tar.bz2 -C /opt && \
    rm /tmp/firefox.tar.bz2 && \
    ln -s /opt/firefox/firefox /usr/local/bin/firefox && \
    chmod +x /opt/firefox/firefox

# Install GeckoDriver for Selenium (architecture-aware)
RUN ARCH=$(uname -m) && \
    echo "Detected architecture: $ARCH" && \
    if [ "$ARCH" = "x86_64" ]; then \
        GECKO_URL="https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        GECKO_URL="https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux-aarch64.tar.gz"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    wget "$GECKO_URL" -O /tmp/geckodriver.tar.gz && \
    tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin/ && \
    chmod +x /usr/local/bin/geckodriver && \
    rm /tmp/geckodriver.tar.gz

# Set up Node.js 22.x (matching .nvmrc)
RUN wget -qO- https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get update && \
    apt-get install -y nodejs && \
    node -v && npm -v && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
ARG APP_DIR="/kath/app"
WORKDIR ${APP_DIR}

# Install Python dependencies
COPY --link ./back_end/requirements.txt ./back_end/requirements.txt
RUN MAKEFLAGS="-j$(nproc)" pip install --no-cache-dir --break-system-packages --root-user-action ignore -r ./back_end/requirements.txt

# Install Node dependencies (including dev dependencies for Vite)
COPY --link ./front_end/package.json ./front_end/package-lock.json ./front_end/
RUN cd ./front_end && npm ci && cd ..

# Create necessary directories and symlinks
RUN mkdir -p ${APP_DIR}/back_end/src/workspace/fasta/ && \
    ln -sf /reference_files/hg38.fa ${APP_DIR}/back_end/src/workspace/fasta/hg38.fa && \
    mkdir -p ${APP_DIR}/back_end/src/workspace/revel/ && \
    ln -sf /reference_files/revel_with_transcript_ids.db ${APP_DIR}/back_end/src/workspace/revel/revel_with_transcript_ids.db && \
    mkdir -p ${APP_DIR}/back_end/instance

# Copy application code
COPY --link . .

# Create volume mount points
VOLUME ["${APP_DIR}/back_end/instance", "${APP_DIR}/back_end/src/workspace"]

# Create and prepare config directory for network configuration
# The config/network_config.yaml was copied in the COPY --link . . above
RUN mkdir -p /config && chmod 777 /config && \
    if [ -f ./config/network_config.yaml ]; then \
      cp ./config/network_config.yaml /config/network_config.yaml; \
    fi

# Expose ports
EXPOSE 5173 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=instance/kath.db
ENV NETWORK_CONFIG_PATH=/config/network_config.yaml
ENV PORT=5173
ENV DOMAIN=localhost

# Health check
# Note: Uses localhost which may need adjustment for remote access
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/monitoring/health || exit 1

# Entry point
ENTRYPOINT ["./run.sh"]
