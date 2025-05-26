from tqdm import tqdm
import fire
from utils import read_jsonl, write_jsonl


def get_query(input_file, output_file):
    data = read_jsonl(input_file)
    queries = []
    for i, line in tqdm(enumerate(data)):
        for j, solution in enumerate(line["split_solutions"]):
            queries.append({
                "question": line["problem"],
                "response": solution,
                "expected_answer": line["expected_answer"],
                "split_data_idx": i,
                "split_idx": j
            })
    write_jsonl(output_file, queries)

def post_process(input_file, response_file, output_file):
    data = read_jsonl(input_file)
    for line in data:
        line["solution_correctness"] = [{} for _ in range(len(line["split_solutions"]))]
    responses = read_jsonl(response_file)
    for line in responses:
        origin_line = data[line["split_data_idx"]]
        origin_line["solution_correctness"][line["split_idx"]] = {
            "correct": line["correct"],
            "llm_correctness": line["llm_correctness"],
            "rule_correctness": line["rule_correctness"],
        }
    write_jsonl(output_file, data)


if __name__ == "__main__":
    fire.Fire()
