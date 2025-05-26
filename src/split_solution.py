from utils import read_jsonl, write_jsonl
import fire
from tqdm import tqdm
from transformers import AutoTokenizer
import re
import os
import json
# get current directory
pwd = os.path.dirname(os.path.abspath(__file__))

prompt = open(f"{pwd}/prompts/split_solution_prompt.txt").read()
icl1_a = open(f"{pwd}/prompts/split_solution_icl_1_a.txt").read()
icl2_q = open(f"{pwd}/prompts/split_solution_icl_2_q.txt").read()
icl2_a = open(f"{pwd}/prompts/split_solution_icl_2_a.txt").read()
icl3_q = open(f"{pwd}/prompts/split_solution_icl_3_q.txt").read()
icl3_a = open(f"{pwd}/prompts/split_solution_icl_3_a.txt").read()
icl4_q = open(f"{pwd}/prompts/split_solution_icl_4_q.txt").read()
icl4_a = open(f"{pwd}/prompts/split_solution_icl_4_a.txt").read()
icl5_q = open(f"{pwd}/prompts/split_solution_icl_5_q.txt").read()
icl5_a = open(f"{pwd}/prompts/split_solution_icl_5_a.txt").read()
icl6_q = open(f"{pwd}/prompts/split_solution_icl_6_q.txt").read()
icl6_a = open(f"{pwd}/prompts/split_solution_icl_6_a.txt").read()
last_prompt = open(f"{pwd}/prompts/split_solution_last_prompt.txt").read()
def get_init_message():
    messages = [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": icl1_a},
        {"role": "user", "content": icl2_q},
        {"role": "assistant", "content": icl2_a},
        {"role": "user", "content": icl3_q},
        {"role": "assistant", "content": icl3_a},
        {"role": "user", "content": icl4_q},
        {"role": "assistant", "content": icl4_a},
        {"role": "user", "content": icl5_q},
        {"role": "assistant", "content": icl5_a},
        {"role": "user", "content": icl6_q},
        {"role": "assistant", "content": icl6_a}
    ]
    return messages
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.3-70B-Instruct")
init_message = get_init_message()
init_length = len(tokenizer.apply_chat_template(init_message, add_generation_prompt=True))

def get_problem(line):
    for key in ["problem", "Question", "question"]:
        if key in line:
            return line[key]
    return None

def get_solution(line):
    for key in ["response", "solution"]:
        if key in line:
            solution = line[key]
            if isinstance(solution, list):
                solution = solution[0]
            # only split the reasoning part
            if "</think>" in solution:
                solution = solution.split("</think>")[0].replace("<think>", "").strip()
            return solution
    return None

# direct split
def get_split_query(input_file, output_file, steps_per_request=50, model="meta-llama/Llama-3.3-70B-Instruct"):
    data = read_jsonl(input_file)
    # for max length
    tokenizer = AutoTokenizer.from_pretrained(model)
    max_tokens = 32768
    queries = []
    for i, line in enumerate(tqdm(data)):
        problem = get_problem(line)
        solution = get_solution(line)
        tmp_queries = []
        
        steps = solution.strip().split("\n\n")
        steps = [s.strip() for s in steps if s.strip()]
        count = 1
        j = 0
        idx = 0
        error_flag = False
        while idx < len(steps):
            step_answer = []
            for step in steps[idx:idx+steps_per_request]:
                step_answer.append("###STEP {}".format(count))
                step_answer.append(step.strip())
                step_answer.append("")
                count += 1
            if len(step_answer) == 0:
                continue
            step_answer = "\n".join(step_answer)
            query = last_prompt.format(question=problem, answer=step_answer)
            messages = get_init_message()
            messages.append({"role": "user", "content": query})
            length = len(tokenizer.apply_chat_template(messages, add_generation_prompt=True))
            max_generation_length = max_tokens - length
            if max_generation_length < 0:
                print("Warning: max generation length is less than 0 in sample {}, split {}".format(i, idx))
                error_flag = True
                break
            tmp_queries.append({
                "messages": messages,
                "max_tokens": max_generation_length,
                "input_idx": i,
                "split_idx": j,
                "step_answer": step_answer,
                "temperature": 0.0
            })
            j += 1
            idx += steps_per_request
        if error_flag:
            continue
        queries.extend(tmp_queries)
    print("Total queries:", len(queries))
    write_jsonl(output_file, queries)

def split_solution(input_file, response_file, processed_file):
    
    def extract_xml(tag_name, text):
        start_tag = f"<{tag_name}>"
        end_tag = f"</{tag_name}>"
        start_idx = text.find(start_tag)
        if start_idx == -1:
            return None
        end_idx = text.find(end_tag)
        if end_idx == -1:
            return None
        return text[start_idx + len(start_tag):end_idx]
    
    def extract_solution(text):
        idxes = get_all_solution_index(text)
        if len(idxes) == 0:
            return None, None, None, None
        if "<solution{}>".format(idxes[0]) in text:
            start_idx = text.find("<solution{}>".format(idxes[0]))
            explanation = text[:start_idx].strip()
        else:
            explanation = None
        
        solutions = []
        steps = []
        answers = []
        completes = []
        for idx in idxes:
            solution = extract_xml("solution{}".format(idx), text)
            if solution is None:
                return None, None, None, None
            step = extract_xml("step", solution)
            answer = extract_xml("answer", solution)
            complete = extract_xml("complete", solution)
            if answer is not None:
                answer = answer.strip()
            if complete is not None:
                complete = complete.strip() == "true"
            else:
                complete = False
            solutions.append(solution)
            steps.append(step)
            answers.append(answer)
            completes.append(complete)
        return explanation, steps, answers, completes
    
    def get_first_and_last_step(text):
        if text is None:
            return None, None
        step_pattern = re.compile(r"###STEP\s+(\d+)\s*\n")
        matches = step_pattern.findall(text)
        if len(matches) == 0:
            return None, None
        first_step = int(matches[0])
        last_step = int(matches[-1])
        return first_step, last_step

    def get_all_solution_index(text):
        solution_pattern = re.compile(r"<solution(\d+)>")
        matches = solution_pattern.findall(text)
        # return all thinking index
        return matches
    
    origin_data = read_jsonl(input_file)
    responses = read_jsonl(response_file)
    
    for line in origin_data:
        line["split_response"] = []
        line["split_range"] = []
    for idx, line in enumerate(responses):
        if len(line["response"]) == 0:
            continue
        origin_line = origin_data[line["input_idx"]]
        origin_line["split_response"].append((line["split_idx"], line["response"]))
        first_step, last_step = get_first_and_last_step(line["step_answer"])
        origin_line["split_range"].append((first_step, last_step))

    for line in origin_data:
        line["split_response"] = sorted(line["split_response"], key=lambda x: x[0])
        line["split_response"] = [x[1] for x in line["split_response"]]

    error = 0
    for line in tqdm(origin_data):
        solution = get_solution(line)
        steps = solution.strip().split("\n\n")
        steps = [s.strip() for s in steps if s.strip()]

        explainations = []
        answers = []
        step_index = []
        results = line["split_response"]
        split_solutions = []
        split_answers = []
        completes = []
        has_error = False
        for r in results:
            # None response
            if r is None:
                has_error = True
                continue
            explanation, solutions, answer, complete = extract_solution(r)
            # no solutions
            if solutions is None:
                has_error = True
                continue
            explainations.append(explanation)
            answers.append(answer)
            completes.append(complete)
            for i, s in enumerate(solutions):
                if not complete[i] or answer[i] is None or answer[i].strip() == "none":
                    continue
                first_step, last_step = get_first_and_last_step(s)
                if last_step is not None:
                    if len(step_index) == 0:
                        step_index.append(last_step)
                        split_answers.append(answer[i])
                    elif last_step > step_index[-1]:
                        step_index.append(last_step)
                        split_answers.append(answer[i])
        if len(step_index) == 0:
            has_error = True
            step_index = [len(steps)]
            new_answers = []
            for a in answers:
                if type(a) == str:
                    new_answers.append(a)
                elif type(a) == list:
                    new_answers.extend(a)
            answers = new_answers
            if not all([a == "none" or a is None for a in answers]):
                split_answers = [[a for a in answers if a != "none" and a is not None][0]]
            else:
                split_answers = ["none"]
        else:
            if step_index[-1] < len(steps):
                step_index[-1] = len(steps)
        for i, idx in enumerate(step_index):
            if i == 0:
                start = 0
            else:
                start = step_index[i-1]
            selected_steps = steps[start:idx]
            selected_steps = "\n\n".join(selected_steps)
            split_solutions.append(selected_steps)
        selected_steps = steps[step_index[-1]:]
        if len(selected_steps) != 0:
            selected_steps = "\n\n".join(selected_steps)
            split_solutions.append(selected_steps)
        # save as stage1 result
        line["split_solutions_stage1"] = split_solutions
        line["explainations_stage1"] = explainations
        line["split_answers_stage1"] = split_answers
        line["full_split_answers_stage1"] = answers
        line["step_index_stage1"] = step_index
        line["split_parse_error_stage1"] = has_error
        line["completes_stage1"] = completes

        # save as final result
        line["split_solutions"] = split_solutions
        line["explainations"] = explainations
        line["split_answers"] = split_answers
        line["full_split_answers"] = answers
        line["step_index"] = step_index
        line["split_parse_error"] = has_error
        line["completes"] = completes

    write_jsonl(processed_file, origin_data)

"""
Additional stage for split solution
Stage2: Find all steps that contain answer
Stage3: Judge whether some split is unnecessary
"""

def extract_json(text):
    start_idx = text.find("```json")
    end_idx = text.rfind("```", start_idx+1)
    if start_idx == -1 or end_idx == -1:
        return None
    text = text[start_idx+len("```json"):end_idx].strip()
    try:
        return json.loads(text)
    except:
        return None
    
stage2_prompt = open(f"{pwd}/prompts/step_judge_prompt.txt").read()
stage2_icl1_a = open(f"{pwd}/prompts/step_judge_icl_1_a.txt").read()
stage2_icl2_q = open(f"{pwd}/prompts/step_judge_icl_2_q.txt").read()
stage2_icl2_a = open(f"{pwd}/prompts/step_judge_icl_2_a.txt").read()
stage2_last_prompt = open(f"{pwd}/prompts/step_judge_last_prompt.txt").read()
def get_stage2_init_message():
    messages = [
        {"role": "user", "content": stage2_prompt},
        {"role": "assistant", "content": stage2_icl1_a},
        {"role": "user", "content": stage2_icl2_q},
        {"role": "assistant", "content": stage2_icl2_a},
    ]
    return messages

# judge whether each step contains the answer
def get_split_solution_stage2_query(input_file, output_file):
    data = read_jsonl(input_file)
    query = []
    for i, line in enumerate(data):
        for j, s in enumerate(line["split_solutions_stage1"]):
            steps = s.split("\n\n")
            for k, step in enumerate(steps):
                if k == len(steps) - 1:
                    continue
                messages = get_stage2_init_message()
                question = get_problem(line)
                messages.append({"role": "user", "content": stage2_last_prompt.format(question=question, answer=step, expected=line["split_answers_stage1"][j])})    
                query.append({
                    "split_id": f"{i}_{j}_{k}",
                    "messages": messages,
                    "temperature": 0.0,
                    "max_tokens": 64
                })        
    print("Num of stage2 query:", len(query))    
    write_jsonl(output_file, query)

def merge_stage2_response(input_file, response_file, output_file):
    data = read_jsonl(input_file)
    response = read_jsonl(response_file)

    result_dict = {line["split_id"]: line for line in response}
    for i, line in enumerate(data):
        new_split_solutions = []
        new_split_answers = []
        temp_split = []
        for j, s in enumerate(line["split_solutions_stage1"]):
            steps = s.split("\n\n")
            for k, step in enumerate(steps):
                temp_split.append(step)
                if k == len(steps) - 1:
                    new_split_solutions.append("\n\n".join(temp_split))
                    new_split_answers.append(line["split_answers_stage1"][j])
                    temp_split = []
                    continue
                split_id = f"{i}_{j}_{k}"
                if split_id in result_dict:
                    try:
                        result = extract_json(result_dict[split_id]["response"])
                        if result["result"]:
                            new_split_solutions.append("\n\n".join(temp_split))
                            new_split_answers.append(line["split_answers_stage1"][j])
                            temp_split = []
                    except:
                        pass                 
        line["split_solutions_stage2"] = new_split_solutions
        line["split_answers_stage2"] = new_split_answers
    write_jsonl(output_file, data)


stage3_prompt = open(f"{pwd}/prompts/split_judge_prompt.txt").read()
stage3_icl1_a = open(f"{pwd}/prompts/split_judge_icl_1_a.txt").read()
stage3_icl2_q = open(f"{pwd}/prompts/split_judge_icl_2_q.txt").read()
stage3_icl2_a = open(f"{pwd}/prompts/split_judge_icl_2_a.txt").read()
stage3_icl3_q = open(f"{pwd}/prompts/split_judge_icl_3_q.txt").read()
stage3_icl3_a = open(f"{pwd}/prompts/split_judge_icl_3_a.txt").read()
stage3_icl4_q = open(f"{pwd}/prompts/split_judge_icl_4_q.txt").read()
stage3_icl4_a = open(f"{pwd}/prompts/split_judge_icl_4_a.txt").read()
stage3_icl5_q = open(f"{pwd}/prompts/split_judge_icl_5_q.txt").read()
stage3_icl5_a = open(f"{pwd}/prompts/split_judge_icl_5_a.txt").read()
stage3_last_prompt = open(f"{pwd}/prompts/split_judge_last_prompt.txt").read()
def get_stage3_init_message():
    messages = [
        {"role": "user", "content": stage3_prompt},
        {"role": "assistant", "content": stage3_icl1_a},
        {"role": "user", "content": stage3_icl2_q},
        {"role": "assistant", "content": stage3_icl2_a},
        {"role": "user", "content": stage3_icl3_q},
        {"role": "assistant", "content": stage3_icl3_a},
        {"role": "user", "content": stage3_icl4_q},
        {"role": "assistant", "content": stage3_icl4_a},
        {"role": "user", "content": stage3_icl5_q},
        {"role": "assistant", "content": stage3_icl5_a},
    ]
    return messages

# judge whether two split should be merged
def get_split_solution_stage3_query(input_file, output_file):
    data = read_jsonl(input_file)
    query = []
    for i, line in enumerate(data):
        if len(line["split_solutions_stage2"]) == 1:
            continue
        for j in range(len(line["split_solutions_stage2"])-1):
            last_split = line["split_solutions_stage2"][j]
            last_split = "\n\n".join(last_split.split("\n\n")[-5:])
            next_split = line["split_solutions_stage2"][j+1]
            next_split = "\n\n".join(next_split.split("\n\n")[:5])
            response = "{}\n<end>\n{}".format(last_split.strip(), next_split.strip())
            messages = get_stage3_init_message()
            question = get_problem(line)
            messages.append({"role": "user", "content": stage3_last_prompt.format(question=question, response=response)})
            length = len(tokenizer.apply_chat_template(messages, add_generation_prompt=True))
            max_generation_length = 32768 - 4096 - length
            if max_generation_length <= 0:
                print("Warning: max generation length is less than 0 in sample {}, split {}".format(i, j))
                continue
            query.append({
                "split_id": f"{i}-{j}",
                "messages": messages,
                "temperature": 0.0,
                "max_tokens": 4096
            })
    print("Number of stage 3 query:", len(query))    
    write_jsonl(output_file, query)


def merge_stage3_response(input_file, response_file, output_file):
    data = read_jsonl(input_file)
    response = read_jsonl(response_file)
    result_dict = {line["split_id"]: line for line in response}
    for i, line in enumerate(data):
        line["idx"] = i
        if len(line["split_solutions_stage2"]) == 1:
            line["split_solutions_stage3"] = line["split_solutions_stage2"]
            line["split_answers_stage3"] = line["split_answers_stage2"]
            continue
        new_split_solutions = []
        new_split_answers = []
        for j in range(len(line["split_solutions_stage2"])):
            if j == 0:
                new_split_solutions.append(line["split_solutions_stage2"][j])
                new_split_answers.append(line["split_answers_stage2"][j])
            else:
                split_id = f"{i}-{j-1}"
                parse_error = False
                try:
                    result = extract_json(result_dict[split_id]["response"])
                except:
                    parse_error = True

                if parse_error or result is None:
                    new_split_solutions.append(line["split_solutions_stage2"][j])
                    new_split_answers.append(line["split_answers_stage2"][j])
                elif "result" in result and result["result"] == False:
                    new_split_solutions[-1] += "\n\n" + line["split_solutions_stage2"][j]
                    new_split_answers[-1] = line["split_answers_stage2"][j]
                else:
                    new_split_solutions.append(line["split_solutions_stage2"][j])
                    new_split_answers.append(line["split_answers_stage2"][j])
        line["split_solutions_stage3"] = new_split_solutions
        line["split_answers_stage3"] = new_split_answers
        # 存储为最终结果
        line["split_solutions"] = new_split_solutions
        line["split_answers"] = new_split_answers
    
    write_jsonl(output_file, data)

def post_process(input_file, response_file, output_file):
    data = read_jsonl(input_file)
    response = read_jsonl(response_file)
    for i, line in enumerate(response):
        data[i]["split_solutions"] = line["split_solutions"]
        data[i]["split_answers"] = line["split_answers"]
    write_jsonl(output_file, data)


if __name__ == "__main__":
    fire.Fire()
