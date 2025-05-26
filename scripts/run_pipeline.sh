set -e

input_file=$1
input_dir=$(dirname $input_file)
input_file_name=$(basename $input_file)
output_file=$2
output_dir=$(dirname $output_file)
model=$3

SCRIPT_DIR=../src
tmp_dir=${output_dir}/ot_tmp
mkdir -p $tmp_dir

### Step 1: Split solution
bash ./run_split_solution.sh \
    ${input_file} \
    ${tmp_dir}/${input_file_name}.split.jsonl

### Step 2: Run math eval for each response
bash ./run_math_eval.sh \
    ${tmp_dir}/${input_file_name}.split.jsonl \
    ${tmp_dir}/${input_file_name}.split.eval.jsonl

### Step 3: Run solution level eval
bash ./run_solution_level_eval.sh \
    ${tmp_dir}/${input_file_name}.split.eval.jsonl \
    ${tmp_dir}/${input_file_name}.split.eval.solution_level_eval.jsonl

### Step 4: Run diversity
bash ./run_diversity.sh \
    ${tmp_dir}/${input_file_name}.split.eval.solution_level_eval.jsonl \
    ${tmp_dir}/${input_file_name}.split.eval.solution_level_eval.diversity.jsonl

### Step 5: Post process and compute metrics
python ${SCRIPT_DIR}/compute_metrics.py prepare_result_file \
    --input_file ${tmp_dir}/${input_file_name}.split.eval.solution_level_eval.diversity.jsonl \
    --output_file ${output_file}

python ${SCRIPT_DIR}/compute_metrics.py compute_metrics \
    --input_file ${output_file} \
    --model ${model}
