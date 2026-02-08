FROM python:3.14-slim

ENV TERM=xterm-256color
ENV COLORTERM=truecolor
ENV COPILOT_CUSTOM_INSTRUCTIONS_DIRS=/home/jacazul/.github/instructions

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    make \
    curl \
    unzip \
    ca-certificates \
    wget \
    jq \
    ripgrep \
    procps \
    fzf \
    htop \
    sudo \
    taskwarrior \
    bc \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install GitHub Copilot CLI
RUN npm install -g @github/copilot

# Install Go
COPY --from=golang:latest /usr/local/go /usr/local/go

ENV PATH=$PATH:/usr/local/go/bin:/root/go/bin

# Create jacazul user
RUN useradd -m -s /bin/bash jacazul && \
    chown -R jacazul:jacazul /home/jacazul && \
    echo "jacazul ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/jacazul && \
    chmod 0440 /etc/sudoers.d/jacazul

USER jacazul
WORKDIR /project

ENTRYPOINT ["copilot"]
