# Slim single-stage image packaging the migration-factory CLI.
FROM python:3.12-slim

# Create an unprivileged user to run the CLI.
RUN useradd --create-home --uid 1000 factory
WORKDIR /app

# Install the package.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir . && rm -rf /root/.cache

USER factory
ENTRYPOINT ["migration-factory"]
CMD ["--help"]
