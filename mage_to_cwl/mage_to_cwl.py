import yaml
from typing import List, Dict, Any
from mage_to_cwl.mage_to_python import MageToPython


class MageToCWL:
    def __init__(self, blocks: List[Dict[str, Any]], pipeline_name: str, repo_name: str) -> None:
        if len(blocks[0]["upstream_blocks"]) > 0:
            raise ValueError("First block must not have an upstream_block!")
        self.blocks = blocks
        self.results: List[MageToPython] = []
        self.files = {f"{pipeline_name}/scripts/requirements/": None}
        self.pipeline_name = pipeline_name
        self.repo_name = repo_name

    def _transform_mage_to_python(self) -> None:
        for i, block in enumerate(self.blocks):
            if i == 0:
                entry = MageToPython(block["content"], block["uuid"], self.repo_name)
                entry.mage_to_python()
                self.results.append(entry)
            else:
                entry = MageToPython(block["content"], block["uuid"], self.repo_name, self.results[i-1].block_name)
                entry.mage_to_python()
                self.results.append(entry)

    class QuotedString(str):
        pass

    @staticmethod
    def _quoted_str_representer(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

    @staticmethod
    def _list_representer(dumper, data):
        return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

    @staticmethod
    def _first_step_template() -> str:
        string = """
        cwlVersion: v1.2
        class: CommandLineTool
        baseCommand: [bash, -c]
        id:
        requirements:
          InlineJavascriptRequirement: {}

        inputs:
          block_name_script:
            type: string
            inputBinding:
              position: 1
          scripts_directory:
            type: Directory
            inputBinding:
              position: 2
          dependency:
            type: File
            inputBinding:
              position: 3

        outputs:
          block_name_result:
            type: File
            outputBinding:
              glob: block_name_result
              
        arguments:
          - valueFrom: |
              set -e && \
              export PYTHONPATH=$(inputs.scripts_directory.path)/requirements:$(inputs.scripts_directory.path)/utils:$PYTHONPATH && \
              python3 $(inputs.scripts_directory.path)/$(inputs.block_name_script)
        
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
        baseCommand: [bash, -c]
        id:
        requirements:
          InlineJavascriptRequirement: {}

        inputs:
          block_name_script:
            type: string
            inputBinding:
              position: 1
          prev_block_name_result:
            type: File
            inputBinding:
              position: 2
          scripts_directory:
            type: Directory
            inputBinding:
              position: 3

        outputs:
          block_name_result:
            type: File
            outputBinding:
              glob: block_name_result
              
        arguments:
          - valueFrom: |
              set -e && \
              export PYTHONPATH=$(inputs.scripts_directory.path)/requirements:$(inputs.scripts_directory.path)/utils:$PYTHONPATH && \
              python3 $(inputs.scripts_directory.path)/$(inputs.block_name_script) $(inputs.prev_block_name_result.path)
        
          - position: 0
            prefix: --
            valueFrom: ""
        """
        return string

    @staticmethod
    def _last_step_template() -> str:
        string = """
            cwlVersion: v1.2
            class: CommandLineTool
            baseCommand: [bash, -c]
            id:
            requirements:
              InlineJavascriptRequirement: {}

            inputs:
              block_name_script:
                type: string
                inputBinding:
                  position: 1
              prev_block_name_result:
                type: File
                inputBinding:
                  position: 2
              scripts_directory:
                type: Directory
                inputBinding:
                  position: 3
                  
            outputs:
              final_output:
                type: File
                outputBinding:
                  glob: final_output

            arguments:
              - valueFrom: |
                  set -e && \
                  export PYTHONPATH=$(inputs.scripts_directory.path)/requirements:$(inputs.scripts_directory.path)/utils:$PYTHONPATH && \
                  python3 $(inputs.scripts_directory.path)/$(inputs.block_name_script) $(inputs.prev_block_name_result.path)

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
    def _install_script() -> Any:
        string = """
        cwlVersion: v1.2
        class: CommandLineTool
        id: install_requirements
        baseCommand: [bash, -c]
        stdout: output
        
        requirements:
          InlineJavascriptRequirement: {}
        
        inputs:
          scripts_folder:
            type: Directory
            inputBinding:
              position: 1
        
        outputs:
          output:
            type: File
            outputBinding:
              glob: output
        
        arguments:
          - valueFrom: |
              set -e
              export PATH=$HOME/.local/bin:$PATH && \
              pip install --user pipreqs && \
              pipreqs $(inputs.scripts_folder.path) --force --ignore $(inputs.scripts_folder.path)/requirements --savepath $(inputs.scripts_folder.path)/requirements/requirements.txt && \
              grep -v '^utils\(==.*\)\?$' $(inputs.scripts_folder.path)/requirements/requirements.txt | sed 's/==.*//' > $(inputs.scripts_folder.path)/requirements/requirements.txt && \
              pip install --target $(inputs.scripts_folder.path)/requirements -r $(inputs.scripts_folder.path)/requirements/requirements.txt
        
          - position: 0
            prefix: --
            valueFrom: ""
        """
        return yaml.safe_load(string)

    @staticmethod
    def _workflow() -> Any:
        string = """
        cwlVersion: v1.2
        class: Workflow
        id: workflow
        
        requirements:
          EnvVarRequirement:
            envDef: {}
        
        inputs:
          scripts_folder:
            type: Directory
        
        outputs:
          install_requirements_result:
            type: File
            outputSource: install_requirements/output
        
        steps:
          install_requirements:
            run: ./steps/install_requirements.cwl
            in:
              scripts_folder: scripts_folder
            out: [output]
        """
        return yaml.safe_load(string)

    @staticmethod
    def _result_displayer() -> str:
        string = """import pickle
import os
import matplotlib.pyplot as plt
import argparse

def display_data(file_path):
    with open(file_path, 'rb') as file:
        data = pickle.load(file)
    
    for var_name, var_value in data.items():
        if isinstance(var_value, plt.Figure):
            os.makedirs("./figures", exist_ok=True)
            plt.savefig(f"./figures/{var_name}.png")
        else:
            print(f"{var_name}: {var_value}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Display data from a pickle file.")
    parser.add_argument('-f', '--file', required=True, help='Path to the pickle file')

    args = parser.parse_args()
    display_data(args.file)
"""
        return string

    @staticmethod
    def _run_script() -> str:
        string = """#! /bin/bash
cwltool --validate workflow.cwl inputs.yml
test_env=$(cat workflow.cwl | grep PLACEHOLDER | wc -l)

if [[ $test_env -ne 0 ]]; then
    echo "Please enter all the environment variables from workflow.cwl file in place of PLACEHOLDER!"
    exit
fi

pip install --target ./scripts/requirements torch --index-url https://download.pytorch.org/whl/cpu

cwltool workflow.cwl inputs.yml && pip install matplotlib && python3 result_displayer.py -f final_output
"""
        return string

    def process(self) -> None:
        self._transform_mage_to_python()
        yaml.representer.SafeRepresenter.add_representer(self.QuotedString, self._quoted_str_representer)
        yaml.representer.SafeRepresenter.add_representer(list, self._list_representer)
        inputs = self._inputs()
        workflow = self._workflow()
        self.files[f"{self.pipeline_name}/result_displayer.py"] = self._result_displayer()
        self.files[f"{self.pipeline_name}/run.sh"] = self._run_script()
        self.files[f"{self.pipeline_name}/steps/install_requirements.cwl"] = yaml.safe_dump(self._install_script(), default_flow_style=False, sort_keys=False)
        for i, result in enumerate(self.results):
            self.files[f"{self.pipeline_name}/scripts/{result.block_name}.py"] = result.code_string
            inputs[f"{result.block_name}_script"] = self.QuotedString(f"{result.block_name}.py")
            workflow["inputs"][f"{result.block_name}_script"] = {
                "type": "string"
            }
            if i == 0:
                template = self._first_step_template().replace("block_name", result.block_name)
                template = template.replace("id:", f"id: {result.block_name}")
                workflow["steps"][result.block_name] = {
                    "run": f"./steps/{result.block_name}.cwl",
                    "in": {
                        f"{result.block_name}_script": f"{result.block_name}_script",
                        "scripts_directory": "scripts_folder",
                        "dependency": "install_requirements/output"
                    },
                    "out": [f"{result.block_name}_result"]
                }
            elif i == len(self.results) - 1:
                template = self._last_step_template()
                template = template.replace("prev_block_name", result.previous_block_name)
                template = template.replace("block_name", result.block_name)
                template = template.replace("id:", f"id: {result.block_name}")
                workflow["steps"][result.block_name] = {
                    "run": f"./steps/{result.block_name}.cwl",
                    "in": {
                        f"{result.block_name}_script": f"{result.block_name}_script",
                        f"{result.previous_block_name}_result": f"{result.previous_block_name}/{result.previous_block_name}_result",
                        "scripts_directory": "scripts_folder"
                    },
                    "out": ["final_output"]
                }
                workflow["outputs"]["final_output"] = {
                    "type": "File",
                    "outputSource": f"{result.block_name}/final_output"
                }
            else:
                template = self._step_template()
                template = template.replace("prev_block_name", result.previous_block_name)
                template = template.replace("block_name", result.block_name)
                template = template.replace("id:", f"id: {result.block_name}")
                workflow["steps"][result.block_name] = {
                    "run": f"./steps/{result.block_name}.cwl",
                    "in": {
                        f"{result.block_name}_script": f"{result.block_name}_script",
                        f"{result.previous_block_name}_result": f"{result.previous_block_name}/{result.previous_block_name}_result",
                        "scripts_directory": "scripts_folder"
                    },
                    "out": [f"{result.block_name}_result"]
                }

            self.files[f"{self.pipeline_name}/steps/{result.block_name}.cwl"] = yaml.safe_dump(yaml.safe_load(template), default_flow_style=False, sort_keys=False)

            for env in result.env_vars:
                if "OUTPUT_FILE" in env:
                    workflow["requirements"]["EnvVarRequirement"]["envDef"][env] = self.QuotedString(f"{env.split('_OUTPUT_FILE')[0].lower()}_result")
                else:
                    workflow["requirements"]["EnvVarRequirement"]["envDef"][env] = self.QuotedString("PLACEHOLDER")

        self.files[f"{self.pipeline_name}/inputs.yml"] = yaml.safe_dump(inputs)
        self.files[f"{self.pipeline_name}/workflow.cwl"] = yaml.safe_dump(workflow, default_flow_style=False, sort_keys=False)
