#!/bin/bash

# delete the dist folder
rm -rf dist
# build
python3 -m build
# check if any .whl files exist in the dist directory
if ls dist/*.whl > /dev/null 2>&1; then
    # if .whl file exists, install the build
    for file in dist/*.whl; do pip install "$file"; done
else
    # if no .whl files exist, print a message and continue
    echo "No .whl files found in dist directory. Skipping installation."
fi