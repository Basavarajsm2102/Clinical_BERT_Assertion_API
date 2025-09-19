#!/bin/bash

# Format fixing script to ensure black and isort compatibility

echo "🔧 Fixing import formatting compatibility..."

# Run isort first with proper configuration
echo "1️⃣ Running isort..."
isort app/ tests/ --profile black --line-length 88 --multi-line 3 --trailing-comma --force-grid-wrap 0 --use-parentheses

# Then run black
echo "2️⃣ Running black..."
black app/ tests/ --line-length 88 --target-version py312

# Verify they agree
echo "3️⃣ Verifying compatibility..."
if git diff --quiet; then
    echo "✅ Success! Black and isort now agree"
else
    echo "⚠️  Some files were modified. Please commit these changes."
    git diff --name-only
fi

echo "🎉 Formatting fix completed!"
