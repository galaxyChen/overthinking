# 使用方式: bash run_split_solution.sh <input_file> <output_file>
# 前置条件：使用pip安装flooding，本脚本依赖服务器请求
# input_file: jsonl format, 每一行必须包含如下两个字段：problem: str, solution: str, 例如：{"problem": "1+1", "solution": "2"}
# output_file: jsonl format，在原来的jsonl文件基础上增加了字段：split_solutions, 代表切分的结果，其它增加的字段见字面义。
# 脚本运行过程中会在输入文件目录下新建一个split_tmp文件夹，用于存放中间文件，最后会删除该文件夹

set -e
SCRIPT_DIR=../src

input_file=$1
input_dir=$(dirname $input_file)
input_file_name=$(basename $input_file)
output_file=$2
output_dir=$(dirname $output_file)
# set tmp dir
tmp_dir=${output_dir}/split_solution_tmp
mkdir -p $tmp_dir

# 1. get query
src_file=$1
# get the dir name of the src_file
output_dir=$(basename $src_file)
true && {
    echo "Running on: ${src_file}"
    echo Getting querys...
    python ${SCRIPT_DIR}/split_solution.py get_split_query \
        --input_file ${input_file} \
        --output_file ${tmp_dir}/${input_file_name}.query
}

true && {
    echo Getting split responses...
    python ${SCRIPT_DIR}/query_llm.py \
    --input_file ${tmp_dir}/${input_file_name}.query \
    --output_file ${tmp_dir}/${input_file_name}.response \
    --model meta-llama/Llama-3.3-70B-Instruct \
    --bs 128
}

true && {
    echo Post processing...
    python ${SCRIPT_DIR}/split_solution.py split_solution \
        --input_file ${input_file} \
        --response_file ${tmp_dir}/${input_file_name}.response \
        --processed_file ${tmp_dir}/${input_file_name}.processed
}

true && {
    echo "Additional process:"
    true && {
        echo Stage 2: get querys...
        python ${SCRIPT_DIR}/split_solution.py get_split_solution_stage2_query \
            --input_file ${tmp_dir}/${input_file_name}.processed \
            --output_file ${tmp_dir}/${input_file_name}.stage2.query
    }

    true && {
        echo Stage 2: Getting split responses...
        python ${SCRIPT_DIR}/query_llm.py \
        --input_file ${tmp_dir}/${input_file_name}.stage2.query \
        --output_file ${tmp_dir}/${input_file_name}.stage2.response \
        --model meta-llama/Llama-3.3-70B-Instruct \
        --bs 128
    }

    true && {
        echo Stage 2: Post processing...
        python ${SCRIPT_DIR}/split_solution.py merge_stage2_response \
            --input_file ${tmp_dir}/${input_file_name}.processed \
            --response_file ${tmp_dir}/${input_file_name}.stage2.response \
            --output_file ${tmp_dir}/${input_file_name}.processed
    }

    true && {
        echo Stage 3: get querys...
        python ${SCRIPT_DIR}/split_solution.py get_split_solution_stage3_query \
            --input_file ${tmp_dir}/${input_file_name}.processed \
            --output_file ${tmp_dir}/${input_file_name}.stage3.query
    }

    true && {
        echo Stage 3: Getting split responses...
        python ${SCRIPT_DIR}/query_llm.py \
        --input_file ${tmp_dir}/${input_file_name}.stage3.query \
        --output_file ${tmp_dir}/${input_file_name}.stage3.response \
        --model meta-llama/Llama-3.3-70B-Instruct \
        --bs 128
    }

    true && {
        echo Stage 3: Post processing...
        python ${SCRIPT_DIR}/split_solution.py merge_stage3_response \
            --input_file ${tmp_dir}/${input_file_name}.processed \
            --response_file ${tmp_dir}/${input_file_name}.stage3.response \
            --output_file ${tmp_dir}/${input_file_name}.processed
    }
}

true && {
    echo "Processing final output..."
    python ${SCRIPT_DIR}/split_solution.py post_process \
        --input_file ${input_file} \
        --response_file ${tmp_dir}/${input_file_name}.processed \
        --output_file ${output_file}
}
