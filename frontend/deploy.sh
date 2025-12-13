#!/bin/bash
set -e

# Deployment script for Frontend
# Usage: ./deploy.sh

# 1. Install Dependencies
echo "Installing dependencies..."
npm install

# 2. Build
echo "Building frontend..."
npm run build

# 3. Output
echo "Build complete. Output is in 'dist/' directory."
