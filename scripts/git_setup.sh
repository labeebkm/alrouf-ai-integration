#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# AL ROUF Assessment — Git Setup & Push Script
# Run this once from the project root after extracting the ZIP.
# ─────────────────────────────────────────────────────────────
set -e

REPO_URL="${1:-}"

if [ -z "$REPO_URL" ]; then
  echo "Usage: bash scripts/git_setup.sh https://github.com/YOUR_USERNAME/alrouf-ai-integration.git"
  exit 1
fi

echo "→ Initialising git repository..."
git init
git add .
git commit -m "feat: initial commit — AL ROUF AI integration assessment

Task 1: RFQ → CRM automation pipeline (23 tests)
Task 2: FastAPI quotation microservice + Docker (24 tests)
Task 3: Bilingual RAG knowledge workflow (26 tests)
Total: 73/73 tests passing, fully offline mock mode"

echo "→ Setting remote origin..."
git remote add origin "$REPO_URL"
git branch -M main

echo "→ Pushing to GitHub..."
git push -u origin main

echo ""
echo "✓ Repository pushed to: $REPO_URL"
echo ""
echo "Now copy your commit hash for the submission PDF:"
git log --oneline -1
