#! /bin/bash
cwltool --validate workflow.cwl inputs.yml
test_env=$(cat workflow.cwl | grep PLACEHOLDER | wc -l)

if [[ $test_env -ne 0 ]]; then
    echo "Please enter all the environment variables from workflow.cwl file in place of PLACEHOLDER!"
    exit
fi

DIR="./scripts/requirements"

if [ -z "$(ls -A "$DIR")" ]; then
    pip install --user pipreqs
    pipreqs ./scripts --force --ignore scripts/requirements --savepath scripts/requirements/requirements.txt
    grep -v '^utils\(==.*\)\?$' ./scripts/requirements/requirements.txt | sed 's/==.*//' > ./scripts/requirements/requirements_parsed.txt
    pip install --target ./scripts/requirements -r ./scripts/requirements/requirements_parsed.txt
fi

cwltool workflow.cwl inputs.yml && pip install --target ./scripts/requirements matplotlib && export PYTHONPATH=./scripts/requirements:./scripts:$PYTHONPATH && python3 result_displayer.py -f final_output
