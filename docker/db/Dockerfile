FROM postgres:15.0-alpine

# Update and upgrade Alpine packages
RUN apk update && \
    apk upgrade

# Install libpq to ensure SNI support
RUN apk add --no-cache libpq