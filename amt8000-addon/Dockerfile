ARG BUILD_FROM
FROM ${BUILD_FROM:-ghcr.io/home-assistant/amd64-base-python:3.12-alpine3.21}

# Install Python dependencies
RUN pip3 install --no-cache-dir flask==3.1.1

# Copy application files
COPY rootfs /

# Make run script executable
RUN chmod a+x /run.sh

# Set working directory
WORKDIR /app

# Default command
CMD [ "/run.sh" ]
