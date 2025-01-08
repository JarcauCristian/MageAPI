cwlVersion: v1.2
class: CommandLineTool
baseCommand: [bash, -c]
id: get_file
requirements:
  InlineJavascriptRequirement: {}
inputs:
  get_file_script:
    type: string
    inputBinding:
      position: 1
  scripts_directory:
    type: Directory
    inputBinding:
      position: 2
outputs:
  get_file_result:
    type: File
    outputBinding:
      glob: get_file_result
arguments: [{valueFrom: 'set -e &&               export PYTHONPATH=$(inputs.scripts_directory.path)/requirements:$(inputs.scripts_directory.path)/utils:$PYTHONPATH
      &&               python3 $(inputs.scripts_directory.path)/$(inputs.get_file_script)

      '}, {position: 0, prefix: --, valueFrom: ''}]
