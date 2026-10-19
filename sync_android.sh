#!/bin/bash
echo "Syncing NSM code to Android..."
mkdir -p android/app/src/main/python
rm -rf android/app/src/main/python/src
rm -rf android/app/src/main/python/static
rm -rf android/app/src/main/python/data
cp -r src android/app/src/main/python/
cp -r static android/app/src/main/python/
mkdir -p android/app/src/main/python/data
cp data/stimuli.txt android/app/src/main/python/data/ 2>/dev/null || true
echo "Done!"
