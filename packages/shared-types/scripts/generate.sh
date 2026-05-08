#!/usr/bin/env bash
set -e

echo "Generating TypeScript interfaces..."
mkdir -p generated/typescript
mkdir -p generated/python

# Generate TypeScript
for schema in schemas/events/*.json; do
  filename=$(basename "$schema" .json)
  npx json2ts -i "$schema" -o "generated/typescript/${filename}.ts"
done

# Generate Python using datamodel-code-generator
# Assumes 'uv' is installed as per MegaIoT standard setup
if ! command -v datamodel-codegen &> /dev/null; then
    echo "Installing datamodel-code-generator..."
    pip install datamodel-code-generator
fi

echo "Generating Python Pydantic models..."
for schema in schemas/events/*.json; do
  filename=$(basename "$schema" .json)
  datamodel-codegen \
    --input "$schema" \
    --input-file-type jsonschema \
    --output "generated/python/${filename}.py" \
    --output-model-type pydantic_v2.BaseModel \
    --target-python-version 3.12
done

echo "Type generation complete."
