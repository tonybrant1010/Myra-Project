# syntax=docker/dockerfile:1













FROM debian:trixie-slim



ARG BRIDGE_VERSION=3.27.1

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        pass \
        socat \
        libsecret-1-0 \
        libfido2-1 \
    && rm -rf /var/lib/apt/lists/*



RUN curl -fsSL -o /tmp/bridge.deb \
        "https://github.com/ProtonMail/proton-bridge/releases/download/v${BRIDGE_VERSION}/protonmail-bridge_${BRIDGE_VERSION}-1_amd64.deb" \
    && apt-get update \
    && apt-get install -y --no-install-recommends /tmp/bridge.deb \
    && rm -f /tmp/bridge.deb \
    && rm -rf /var/lib/apt/lists/*

COPY gpg-key-params /gpg-key-params
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh



ENV HOME=/root
WORKDIR /root
VOLUME ["/root"]



EXPOSE 25

ENTRYPOINT ["/entrypoint.sh"]
CMD ["run"]
