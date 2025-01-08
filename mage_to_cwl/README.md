# Mage To CWL
Helper Python scripts to convert Mage AI pipelines to CWL.

## Usage
```python
from mage_to_cwl import MageToCWL
import zipfile

blocks = [{
  "name": "...",
  "upstream_blocks": ["...", "..."],
  "downstream_blocks": ["...", "..."],
  "content": "<code_string>"
}, ...]

# Creating MageToCWL object with a list of blocks from a Mage AI pipeline
mtc = MageToCWL(blocks, pipeline_name=..., repo_name="default_repo")

# Run the transformation process to get the CWL files
mtc.process()

with zipfile.ZipFile("result.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
  for file_path, content in mtc.files.items():
    if content is None:
      zipf.writestr(file_path, '')
    else:
      zipf.writestr(file_path, content)
```
