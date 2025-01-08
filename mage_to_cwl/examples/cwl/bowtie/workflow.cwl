cwlVersion: v1.2
class: Workflow
id: workflow
requirements:
  EnvVarRequirement:
    envDef:
      READ_FASTA_OUTPUT_FILE: "read_fasta_result"
      GENOME: "fmr1"
inputs:
  scripts_folder:
    type: Directory
  read_fasta_script:
    type: string
  export_bowtie_script:
    type: string
outputs:
  final_output:
    type: File
    outputSource: export_bowtie/final_output
steps:
  read_fasta:
    run: ./steps/read_fasta.cwl
    in:
      read_fasta_script: read_fasta_script
      scripts_directory: scripts_folder
    out: [read_fasta_result]
  export_bowtie:
    run: ./steps/export_bowtie.cwl
    in:
      export_bowtie_script: export_bowtie_script
      read_fasta_result: read_fasta/read_fasta_result
      scripts_directory: scripts_folder
    out: [final_output]
