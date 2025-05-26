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

# generate query
python ${SCRIPT_DIR}/solution_level_eval.py get_query \
--input_file ${input_file} \
--output_file ${tmp_dir}/${input_file_name}.solution_level_query.jsonl

# generate response
bash ./run_math_eval.sh \
${tmp_dir}/${input_file_name}.solution_level_query.jsonl \
${tmp_dir}/${input_file_name}.solution_level_response.jsonl

# post processed
python ${SCRIPT_DIR}/solution_level_eval.py post_process \
--input_file ${input_file} \
--response_file ${tmp_dir}/${input_file_name}.solution_level_response.jsonl \
--output_file ${output_file}
