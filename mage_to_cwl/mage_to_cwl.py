from typing import List, Dict, Any
from mage_to_cwl.mage_to_python import MageToPython


class MageToCWL:
    def __init__(self, blocks: List[Dict[str, Any]]) -> None:
        if len(blocks[0]["upstream_blocks"]) > 0:
            raise ValueError("First block must not have an upstream_block!")
        self.blocks = blocks
        self.results: List[MageToPython] = []
        self.files = []

    def _transform_mage_to_python(self):
        for i, block in enumerate(self.blocks):
            if i == 0:
                entry = MageToPython(block["content"], block["uuid"])
                entry.mage_to_python()
                self.results.append(entry)
            else:
                entry = MageToPython(block["content"], block["uuid"], self.results[i-1].block_name, self.results[i-1].output_type)
                entry.mage_to_python()
                self.results.append(entry)

    @staticmethod
    def _first_step_template():
        string = """
        cwlVersion: v1.2
        class: CommandLineTool
        
        baseCommand: python3
        
        inputs:
          block_name:
            type: File
            inputBinding:
              position: 1
        
        outputs:
          block_name:
            type: File
            outputBinding:
              glob: block_name
        """
        return string

    @staticmethod
    def _step_template():
        string = """
        cwlVersion: v1.2
        class: CommandLineTool

        baseCommand: python3

        inputs:
          block_name:
            type: File
            inputBinding:
              position: 1
          prev_block_name:
            type: File
            inputBinding:
              position: 2 

        outputs:
          block_name:
            type: File
            outputBinding:
              glob: block_name
        """
        return string

    @staticmethod
    def _last_step_template():
        string = """
        cwlVersion: v1.2
        class: CommandLineTool

        baseCommand: python3

        inputs:
          block_name:
            type: File
            inputBinding:
              position: 1
          prev_block_name:
            type: File
            inputBinding:
              position: 2 

        outputs: []
        """
        return string

    def process(self):
        self._transform_mage_to_python()
        for i, result in enumerate(self.results):
            if i == 0:
                template = self._first_step_template().replace("block_name", result.block_name)
                self.files.append(template)
            elif i == len(self.results) - 1:
                template = self._last_step_template()
                template = template.replace("block_name", result.block_name)
                template = template.replace("prev_block_name", result.previous_block_name)
                self.files.append(template)
            else:
                template = self._step_template()
                template = template.replace("block_name", result.block_name)
                template = template.replace("prev_block_name", result.previous_block_name)
                self.files.append(template)

