from utils import read_jsonl, write_jsonl
import fire
from transformers import AutoTokenizer
import numpy as np

def prepare_result_file(input_file, output_file):
    """
    Prepare the result file by reading the input file and writing it to the output file.
    """
    data = read_jsonl(input_file)
    new_data = []
    for line in data:
        item = {
            "problem": line["problem"],
            "response": line["response"],
            "expected_answer": line["expected_answer"],
            "correct": line["correct"],
            "split_solutions": []
        }
        assert len(line["split_solutions"]) == len(line["solution_correctness"]) == len(line["cluster_ids"])
        for i in range(len(line["split_solutions"])):
            item["split_solutions"].append({
                "solution": line["split_solutions"][i],
                "correct": line["solution_correctness"][i]["correct"],
                "cluster": line["cluster_ids"][i]
            })
            new_data.append(item)
    write_jsonl(output_file, new_data)


def get_outcome_efficiency(line):
    """
    line: {
        "split_solutions": [
            {
                "solution": "solution text",
                "correct": True/False,
                "cluster": int,
                "length": int
            },
            ...
        ],
    }
    """
    correct_round = []
    correct_ratio = int(any([s["correct"] for s in line["split_solutions"]]))
    for i, s in enumerate(line["split_solutions"]):
        correct_round.append(s)
        if s["correct"]:
            break
    correct_tokens = sum([s["length"] for s in correct_round])
    all_tokens = sum([s["length"] for s in line["split_solutions"]])
    outcome_efficiency = correct_ratio * correct_tokens / all_tokens
    return outcome_efficiency

def get_process_efficiency(line):
    existing_clusters = set()
    diverse_tokens = []
    correct_ratio = []
    for s in line["split_solutions"]:
        if "cluster" not in s:
            s["cluster"] = 0
        if s["cluster"] not in existing_clusters:
            existing_clusters.add(s["cluster"])
            diverse_tokens.append(s["length"])
            correct_ratio.append(s["correct"])
    all_tokens = sum([s["length"] for s in line["split_solutions"]])
    process_efficiency = sum(diverse_tokens) / all_tokens
    return process_efficiency

def compute_metrics(input_file, model):
    tokenzier = AutoTokenizer.from_pretrained(model)
    data = read_jsonl(input_file)

    pe = []
    oe = []
    for line in data:
        # compute length of each solution
        for s in line["split_solutions"]:
            s["length"] = len(tokenzier.encode(s["solution"], add_special_tokens=False))
        
        # compute outcome efficiency
        oe.append(get_outcome_efficiency(line))
        
        # compute process efficiency
        pe.append(get_process_efficiency(line))
    oe_score = np.mean(oe)
    pe_score = np.mean(pe)
    print("Average Solutions:", np.mean([len(line["split_solutions"]) for line in data]))
    print(f"Outcome Efficiency: {oe_score:.4f}")
    print(f"Process Efficiency: {pe_score:.4f}")


if __name__ == "__main__":
    fire.Fire()
