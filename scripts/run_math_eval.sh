set -e
input_file=$1
input_dir=$(dirname $input_file)
input_file_name=$(basename $input_file)
output_file=$2
output_dir=$(dirname $output_file)
SCRIPT_DIR=../src

# set tmp dir
tmp_dir=${output_dir}/math_eval_tmp
mkdir -p $tmp_dir

true && {
    echo "Generating extract answer query for $input_file"
    python ${SCRIPT_DIR}/extract_and_eval.py get_extract_answer_query \
    --input_file $input_file \
    --output_file $tmp_dir/${input_file_name}.extract_answer_query.jsonl
}

true && {
    echo "Getting response for extract answer query"
    python ${SCRIPT_DIR}/query_llm.py \
    --input_file $tmp_dir/${input_file_name}.extract_answer_query.jsonl \
    --output_file $tmp_dir/${input_file_name}.extract_answer_response.jsonl \
    --model meta-llama/Llama-3.3-70B-Instruct \
    --bs 128
}

true && {
    echo "Extracting answer response"
    python ${SCRIPT_DIR}/extract_and_eval.py extract_answer \
    --origin_file $input_file \
    --response_file $tmp_dir/${input_file_name}.extract_answer_response.jsonl \
    --output_file $tmp_dir/${input_file_name}.processed.jsonl
}

true && {
    echo "Generating judge query"
    python ${SCRIPT_DIR}/extract_and_eval.py get_judge_query \
    --input_file $tmp_dir/${input_file_name}.processed.jsonl \
    --output_file $tmp_dir/${input_file_name}.judge_query.jsonl
}

true && {
    echo "Getting response for judge query"
    python ${SCRIPT_DIR}/query_llm.py \
    --input_file $tmp_dir/${input_file_name}.judge_query.jsonl \
    --output_file $tmp_dir/${input_file_name}.judge_response.jsonl \
    --model KbsdJames/Omni-Judge \
    --bs 128 \
    --completion True
}

true && {
    echo "Extracting judge response"
    python ${SCRIPT_DIR}/extract_and_eval.py judge \
    --input_file $tmp_dir/${input_file_name}.processed.jsonl \
    --response_file $tmp_dir/${input_file_name}.judge_response.jsonl \
    --output_file $output_file
}
