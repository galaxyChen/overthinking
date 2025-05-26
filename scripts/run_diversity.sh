set -e
input_file=$1
output_file=$2
output_dir=$(dirname $output_file)
tmp_dir=${output_dir}/diversity_tmp
mkdir -p $tmp_dir
SCRIPT_DIR=../src

true && {
    echo Getting querys...
    python ${SCRIPT_DIR}/diversity_cluster.py get_query \
    --input_file ${input_file} \
    --output_file ${tmp_dir}/cluster_query.jsonl
}

true && {
    echo Getting response...
    python ${SCRIPT_DIR}/query_llm.py \
    --input_file ${tmp_dir}/cluster_query.jsonl \
    --output_file ${tmp_dir}/cluster_response.jsonl \
    --model gpt-4o-mini \
    --bs 128
}

true && {
    echo Post processing...
    python ${SCRIPT_DIR}/diversity_cluster.py post_processing \
    --origin_file ${input_file} \
    --response_file ${tmp_dir}/cluster_response.jsonl \
    --output_file ${output_file}
}
