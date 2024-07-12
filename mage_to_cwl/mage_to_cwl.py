from typing import List, Dict, Any

import yaml

from mage_to_cwl.mage_to_python import MageToPython


class MageToCWL:
    def __init__(self, blocks: List[Dict[str, Any]]) -> None:
        if len(blocks[0]["upstream_blocks"]) > 0:
            raise ValueError("First block must not have an upstream_block!")
        self.blocks = blocks
        self.results: List[MageToPython] = []
        self.files = {"scripts/requirements/": None}

    def _transform_mage_to_python(self) -> None:
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
    def _first_step_template() -> str:
        string = """
        cwlVersion: v1.2
        class: CommandLineTool
        id:
        baseCommand: [bash, -c]

        inputs:
          block_name:
            type: string
            inputBinding:
              position: 1
          scripts_directory:
            type: string
            inputBinding:
              position: 2

        outputs:
          block_name:
            type: File
            outputBinding:
              glob: block_name
              
        arguments:
          - valueFrom: |
              set -e && \
              export PYTHONPATH=$2:$PYTHONPATH && \
              python $(inputs.scripts_directory.path)/$(inputs.block_name)
        
          - position: 0
            prefix: --
            valueFrom: ""
        """
        return string

    @staticmethod
    def _step_template() -> str:
        string = """
        cwlVersion: v1.2
        class: CommandLineTool
        id:
        baseCommand: [bash, -c]

        inputs:
          block_name:
            type: string
            inputBinding:
              position: 1
          prev_block_name:
            type: string
            inputBinding:
              position: 2
          scripts_directory:
            type: string
            inputBinding:
              position: 3

        outputs:
          block_name:
            type: File
            outputBinding:
              glob: block_name
              
        arguments:
          - valueFrom: |
              set -e && \
              export PYTHONPATH=$3:$PYTHONPATH && \
              python $(inputs.scripts_directory.path)/$(inputs.block_name)
        
          - position: 0
            prefix: --
            valueFrom: ""
        """
        return string

    @staticmethod
    def _inputs() -> Any:
        string = """
        scripts_folder:
            class: Directory
            path: ./scripts
        """
        return yaml.safe_load(string)

    @staticmethod
    def _install_script() -> str:
        string = """
        cwlVersion: v1.2
        class: CommandLineTool
        id: install_requirements
        baseCommand: [bash, -c]
        
        requirements:
          InlineJavascriptRequirement: {}
        
        inputs:
          scripts_folder:
            type: Directory
            inputBinding:
              position: 1
        
        outputs:
          requirements_file:
            type: File
            outputBinding:
              glob: scripts/requirements.txt
        
        arguments:
          - valueFrom: |
              set -e
              export PATH=$HOME/.local/bin:$PATH && \
              pip install --user pipreqs && \
              pipreqs --force $1/requirements && \
              pip install --target $1/requirements -r $1/requirements/requirements.txt
        
          - position: 0
            prefix: --
            valueFrom: ""
        """
        return string

    @staticmethod
    def _workflow() -> Any:
        string = """
        cwlVersion: v1.2
        class: Workflow
        id: workflow
        inputs:
          scripts_folder:
            type: Directory
        
        outputs: []
        
        steps:
          install_requirements:
            run: ./steps/install_requirements.cwl
            in:
              scripts_folder: scripts_folder
            out: [requirements_file]
        """
        return yaml.safe_load(string)

    def process(self) -> None:
        self._transform_mage_to_python()
        inputs = self._inputs()
        workflow = self._workflow()
        self.files["install_requirements.cwl"] = self._install_script()
        for i, result in enumerate(self.results):
            self.files[f"scripts/{result.block_name}.py"] = result.code_string
            inputs[result.block_name] = f"{result.block_name}.py"
            workflow["inputs"][result.block_name] = {
                "type": "string"
            }
            workflow["outputs"][result.block_name] = {
                "type": "File",
                "outputSource": f"{result.block_name}/{result.block_name}"
            }
            if i == 0:
                template = self._first_step_template().replace("block_name", result.block_name)
                template = template.replace("id:", f"id: {result.block_name}")
                workflow["steps"][result.block_name] = {
                    "run": f"./steps/{result.block_name}.cwl",
                    "in": {
                        result.block_name: result.block_name,
                        "scripts_directory": "scripts_folder"
                    },
                    "out": [result.block_name]
                }
            else:
                template = self._step_template()
                template = template.replace("prev_block_name", result.previous_block_name)
                template = template.replace("block_name", result.block_name)
                template = template.replace("id:", f"id: {result.block_name}")
                workflow["steps"][result.block_name] = {
                    "run": f"./steps/{result.block_name}.cwl",
                    "in": {
                        result.block_name: result.block_name,
                        result.previous_block_name: result.previous_block_name,
                        "scripts_directory": "scripts_folder"
                    },
                    "out": [result.block_name]
                }

            self.files[f"steps/{result.block_name}.cwl"] = template

        self.files[f"inputs.yml"] = yaml.safe_dump(inputs)
        self.files[f"workflow.cwl"] = yaml.safe_dump(workflow)

