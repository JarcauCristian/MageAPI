cwlVersion: v1.2
class: CommandLineTool
baseCommand: [bash, -c]
id: read_fasta
requirements:
  InlineJavascriptRequirement: {}
inputs:
  read_fasta_script:
    type: string
    inputBinding:
      position: 1
  scripts_directory:
    type: Directory
    inputBinding:
      position: 2
outputs:
  read_fasta_result:
    type: File
    outputBinding:
      glob: read_fasta_result
arguments: [{valueFrom: 'set -e &&               export PYTHONPATH=$(inputs.scripts_directory.path)/requirements:$(inputs.scripts_directory.path)/utils:$PYTHONPATH
      &&               python3 $(inputs.scripts_directory.path)/$(inputs.read_fasta_script)

      '}, {position: 0, prefix: --, valueFrom: ''}]
