from utils import read_jsonl, write_jsonl, extract_answer_boxed
from openmathinst_utils import math_equal
from tqdm import tqdm
from transformers import AutoTokenizer
import fire
import os

# Get the directory of the current Python script
current_dir = os.path.dirname(os.path.realpath(__file__))
extract_prompt = open("{}/prompts/extract_answer_prompt.txt".format(current_dir)).read()
extract_prompt_icl1_a = open("{}/prompts/extract_answer_icl_1_a.txt".format(current_dir)).read()
extract_prompt_icl2_q = open("{}/prompts/extract_answer_icl_2_q.txt".format(current_dir)).read()
extract_prompt_icl2_a = open("{}/prompts/extract_answer_icl_2_a.txt".format(current_dir)).read()
extract_prompt_icl3_q = open("{}/prompts/extract_answer_icl_3_q.txt".format(current_dir)).read()
extract_prompt_icl3_a = open("{}/prompts/extract_answer_icl_3_a.txt".format(current_dir)).read()
extract_prompt_icl4_q = open("{}/prompts/extract_answer_icl_4_q.txt".format(current_dir)).read()
extract_prompt_icl4_a = open("{}/prompts/extract_answer_icl_4_a.txt".format(current_dir)).read()
extract_prompt_last = open("{}/prompts/extract_answer_last_prompt.txt".format(current_dir)).read()
def get_extract_answer_init_message():
    messages = [
        {"role": "user", "content": extract_prompt},
        {"role": "assistant", "content": extract_prompt_icl1_a},
        {"role": "user", "content": extract_prompt_icl2_q},
        {"role": "assistant", "content": extract_prompt_icl2_a},
        {"role": "user", "content": extract_prompt_icl3_q},
        {"role": "assistant", "content": extract_prompt_icl3_a},
        {"role": "user", "content": extract_prompt_icl4_q},
        {"role": "assistant", "content": extract_prompt_icl4_a},
    ]
    return messages

def get_question(line):
    for key in ["problem", "question", "Question"]:
        if key in line:
            return line[key]

def get_extract_answer_query(input_file, output_file):
    # each line in input_file: {"problem": "problem text", "response": ["response text"]}
    # tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.3-70B-Instruct")
    tokenizer = AutoTokenizer.from_pretrained("/apdcephfs_qy3/share_301812049/shared/model/meta-llama/Llama-3.3-70B-Instruct")
    def get_messages(question, answer):
        messages = get_extract_answer_init_message()
        if type(question) != str or type(answer) != str:
            print("Warning: Question or answer not string", question, answer)
        query = extract_prompt_last.replace("{question}", question).replace("{answer}", answer)
        messages.append({"role": "user", "content": query})
        return messages
    
    def get_query_line(question, solution, idx):
        solution = tokenizer.decode(tokenizer.encode(solution, add_special_tokens=False)[-1024:])
        messages = get_messages(question, solution)
        # if max_generation_length < 0:
        #     print("Warning: Example too long for {}, truncating".format(idx))
        #     solution = tokenizer.encode(solution, add_special_tokens=False)[-1024:]
        #     messages = get_messages(question, tokenizer.decode(solution))
        return {
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0,
        }

    data = read_jsonl(input_file)
    queries = []
    for i, line in enumerate(tqdm(data)):
        question = get_question(line)
        solution = line["response"]
        if type(solution) == list:
            solution = solution[0]
        if "\\boxed{" not in solution:
            query_line = get_query_line(question, solution, "{}-{}".format(i, "response"))
            query_line["type"] = "response"
            query_line["input_idx"] = i
            queries.append(query_line)
        if "expected_answer" not in line:
            solution = line["solution"]
            if "\\boxed{" not in solution:
                query_line = get_query_line(question, solution, "{}-{}".format(i, "solution"))
                query_line["type"] = "solution"
                query_line["input_idx"] = i
                queries.append(query_line)
                
    print("Num of query:", len(queries))
    for i, line in enumerate(queries):
        line["data_idx"] = i

    write_jsonl(output_file, queries)

def extract_answer(origin_file, response_file, output_file):
    data = read_jsonl(origin_file)
    responses = read_jsonl(response_file)
    for line in data:
        line["extract_answer_response"] = None
        response = line["response"]
        if type(response) == list:
            response = response[0]
        line["extracted_answer"] = extract_answer_boxed(response)
        if "expected_answer" not in line:
            line["expected_answer"] = extract_answer_boxed(line["solution"])

    for line in responses:
        if len(line["response"]) == 0:
            continue

        origin_line = data[line["input_idx"]]
        extracted_answer = extract_answer_boxed(line["response"])
        if extracted_answer is None:
            extracted_answer = line["response"]
        if extracted_answer.upper() == "ANSWER NOT FOUND":
            extracted_answer = None
            
        if line["type"] == "response":
            origin_line["extracted_answer"] = extracted_answer
        elif line["type"] == "solution":
            origin_line["expected_answer"] = extracted_answer
    
    # post process
    def post_process(answer):
        if answer is None:
            return None
        answer = answer.replace("\\dfrac{", "\\frac{")
        return answer
    for line in data:
        line["extracted_answer"] = post_process(line["extracted_answer"])
        line["expected_answer"] = post_process(line["expected_answer"])
    write_jsonl(output_file, data)

def get_judge_query(input_file, output_file):
    data = read_jsonl(input_file)
    tokenizer = AutoTokenizer.from_pretrained("KbsdJames/Omni-Judge", trust_remote_code=True)
    queries = []
    for i, line in enumerate(tqdm(data)):
        question = get_question(line)
        expected_answer = line["expected_answer"]
        extracted_answer = line["extracted_answer"]
        if extracted_answer is None or expected_answer is None:
            continue
        extracted_answer_tokens = tokenizer.encode(extracted_answer, add_special_tokens=False)
        if len(extracted_answer_tokens) > 1024:
            extracted_answer = tokenizer.decode(extracted_answer_tokens[-1024:])
        expected_answer_tokens = tokenizer.encode(expected_answer, add_special_tokens=False)
        if len(expected_answer_tokens) > 1024:
            expected_answer = tokenizer.decode(expected_answer_tokens[-1024:])
        prompt = tokenizer.get_context(question, expected_answer, extracted_answer)
        if len(tokenizer.encode(prompt, add_special_tokens=False)) > 7800:
            continue
        queries.append({
            "prompt": prompt,
            "extracted_answer": extracted_answer,
            "expected_answer": expected_answer,
            "temperature": 0,
            "max_tokens": 300,
            "origin_idx": i,
        })
    print("Num of query:", len(queries))
    write_jsonl(output_file, queries)

def judge(input_file, response_file, output_file):
    data = read_jsonl(input_file)
    responses = read_jsonl(response_file)
    tokenizer = AutoTokenizer.from_pretrained("KbsdJames/Omni-Judge", trust_remote_code=True)
    for line in tqdm(data):
        try:
            line["rule_correctness"] = math_equal(line["extracted_answer"], line["expected_answer"])
        except:
            line["rule_correctness"] = False
        line["llm_correctness"] = False

    for line in responses:
        if len(line["response"]) == 0:
            continue
        origin_line = data[line["origin_idx"]]
        try:
            judge_res = tokenizer.parse_response(line["response"])
        except Exception as e:
            judge_res = "Failed to parse"
        origin_line["judge_res"] = judge_res
        if judge_res != "Failed to parse":
            origin_line["llm_correctness"] = judge_res["judgement"] == "TRUE"
    
    for line in data:
        extracted_answer = line["extracted_answer"]
        expected_answer = line["expected_answer"]
        if extracted_answer is not None and expected_answer is not None:
            # string equal
            if extracted_answer.strip() == expected_answer.strip():
                line["correct"] = True
                continue
            if extracted_answer.isnumeric() and expected_answer.isnumeric():
                # numeric equal: use rule correctness
                line["correct"] = line["rule_correctness"]
                continue
        if extracted_answer is None:
            # non-finished response: False
            line["correct"] = False
            continue
        if line["rule_correctness"]:
            # set high correct priority for correct rule correctness
            line["correct"] = True
            continue
        # default to llm correctness
        line["correct"] = line["llm_correctness"]
    print("llm acc:", sum([line["llm_correctness"] for line in data]) / len(data))
    print("rule acc:", sum([line["rule_correctness"] for line in data]) / len(data))
    print("acc:", sum([line["correct"] for line in data]) / len(data))
    write_jsonl(output_file, data)


if __name__ == "__main__":
    fire.Fire()
