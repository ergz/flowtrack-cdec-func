#!/bin/bash

# Function to print usage
print_usage() {
  echo "Usage: $0 [--full]"
  echo "  --full    Perform a full rebuild, including reinstalling all dependencies"
}

# Parse command line arguments
FULL_BUILD=false
while [[ "$#" -gt 0 ]]; do
  case $1 in
  --full) FULL_BUILD=true ;;
  -h | --help)
    print_usage
    exit 0
    ;;
  *)
    echo "Unknown parameter: $1"
    print_usage
    exit 1
    ;;
  esac
  shift
done

# Ensure we're in the project directory
cd "$(dirname "$0")"

# Create package directory if it doesn't exist
mkdir -p package

if [ "$FULL_BUILD" = true ]; then
  echo "Performing full build..."
  rm -rf package/*
  uv pip install --target ./package -r requirements.txt
  cd package
  zip -r ../flowtrack-aggregator.zip .
  cd ..
else
  echo "Updating Python file only..."
fi

# Always update the Python file in the zip
zip -g flowtrack-aggregator.zip lambda_function.py

echo "Build complete: flowtrack-aggregator.zip"
