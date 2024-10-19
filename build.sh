#! /bin/bash

mkdir -p package
uv pip install --target ./package -r requirements.txt
cd package
zip -r ../flowtrack-aggregator.zip .
cd ..
zip flowtrack-aggregator.zip lambda_function.py
