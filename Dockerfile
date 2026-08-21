FROM python:3.12-slim

# Install Node (for the Vercel CLI) + git.
#
# netlify-cli was removed in the 2026-08 migration. If DEPLOY_TARGET=netlify is
# ever used to roll back, this image cannot serve it — add netlify-cli back and
# rebuild first. The env-var switch alone is not enough.
RUN apt-get update && apt-get install -y curl git && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g vercel@54.18.0 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the pipeline
CMD ["python3", "scripts/run_pipeline.py"]
