cwlVersion: v1.2
class: CommandLineTool
baseCommand: [bash, -c]
id: wise_cloud
requirements:
  InlineJavascriptRequirement: {}
inputs:
  wise_cloud_script:
    type: string
    inputBinding:
      position: 1
  get_file_result:
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
arguments: [{valueFrom: 'set -e &&                   export PYTHONPATH=$(inputs.scripts_directory.path)/requirements:$(inputs.scripts_directory.path)/utils:$PYTHONPATH
      &&                   python3 $(inputs.scripts_directory.path)/$(inputs.wise_cloud_script)
      $(inputs.get_file_result.path)

      '}, {position: 0, prefix: --, valueFrom: ''}]
