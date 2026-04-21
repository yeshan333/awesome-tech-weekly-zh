#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "==> Pulling latest changes..."
# Stash any local changes to avoid pull conflicts, then restore
if ! git diff --quiet HEAD || ! git diff --cached --quiet; then
    git stash push -m "auto-stash-before-deploy-$(date +%s)" --include-untracked
    git pull origin main
    git stash pop || true
else
    git pull origin main
fi

echo "==> Building site..."
python3 scripts/build_site.py

echo "==> Deploying to Netlify..."

if [ -f ".env" ]; then
    source ".env"
fi

if [ -z "$NETLIFY_AUTH_TOKEN" ] || [ -z "$NETLIFY_SITE_ID" ]; then
    echo "Error: NETLIFY_AUTH_TOKEN and NETLIFY_SITE_ID must be set."
    echo "Add them to .env in the project root:"
    echo '  NETLIFY_AUTH_TOKEN=your-token'
    echo '  NETLIFY_SITE_ID=your-site-id'
    exit 1
fi

npx netlify-cli deploy --prod \
    --site="$NETLIFY_SITE_ID" \
    --auth="$NETLIFY_AUTH_TOKEN" \
    --dir=site \
    --no-build \
    --message="Deploy AI Gen Site $(date +%Y-%m-%d)"

echo "==> Deploy complete."
