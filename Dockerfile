FROM python:3.12-slim

# Install Node (for both deploy CLIs) + git.
#
# BOTH CLIs are installed on purpose, for the duration of the Netlify -> Vercel
# migration. publish.py picks between them from DEPLOY_TARGET, and the point of
# that switch is that a rollback is a Railway variable change taking effect on
# the very next cron run. If only one CLI were present the switch would need an
# image rebuild first, which is exactly the delay you cannot afford at the
# moment you discover the new platform is wrong.
#
# Cost is about 30s of build time and some image size. Once Vercel has run
# clean for a few weeks, drop netlify-cli and this comment together.
RUN apt-get update && apt-get install -y curl git && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g vercel@54.18.0 netlify-cli@25.6.0 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the pipeline
CMD ["python3", "scripts/run_pipeline.py"]
