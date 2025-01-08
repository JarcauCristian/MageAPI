cwlVersion: v1.2
class: Workflow
id: workflow
requirements:
  EnvVarRequirement:
    envDef:
      GET_FILE_OUTPUT_FILE: "get_file_result"
inputs:
  scripts_folder:
    type: Directory
  get_file_script:
    type: string
  wise_cloud_script:
    type: string
outputs:
  final_output:
    type: File
    outputSource: wise_cloud/final_output
steps:
  get_file:
    run: ./steps/get_file.cwl
    in:
      get_file_script: get_file_script
      scripts_directory: scripts_folder
    out: [get_file_result]
  wise_cloud:
    run: ./steps/wise_cloud.cwl
    in:
      wise_cloud_script: wise_cloud_script
      get_file_result: get_file/get_file_result
      scripts_directory: scripts_folder
    out: [final_output]
