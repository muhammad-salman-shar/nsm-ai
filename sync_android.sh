#!/bin/bash
# Sync NSM code into Android Python folder
echo "Syncing NSM code to Android..."
mkdir -p android/app/src/main/python
rm -rf android/app/src/main/python/src
rm -rf android/app/src/main/python/static
cp -r src android/app/src/main/python/
cp -r static android/app/src/main/python/
echo "Done!"
