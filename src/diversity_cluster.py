import re
import fire
from utils import read_jsonl, write_jsonl
import os

pwd = os.path.dirname(os.path.abspath(__file__))
prompt1 = open(f"{pwd}/prompts/diversity_prompt_1.txt").read()
prompt2 = open(f"{pwd}/prompts/diversity_prompt_2.txt").read()

def get_problem(line):
    for key in ["problem", "Question", "question"]:
        if key in line:
            return line[key]
    return None

def get_query(input_file, output_file):
    data = read_jsonl(input_file)
    queries = []
    for i, line in enumerate(data):
        prompt = ""
        for idx, s in enumerate(line["split_solutions"]):
            prompt = prompt + "Solution " + str(idx+1) + ":\n" + s + "\n"
        question_prompt = prompt1.replace("***problem***", get_problem(line))
        final_prompt = question_prompt + prompt + prompt2
        queries.append({
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": final_prompt},
            ],
            "metadata": {"data_idx": i}
        })
    print("Total number of queries: {}".format(len(queries)))
    write_jsonl(output_file, queries)

def post_processing(origin_file, response_file, output_file):
    import ast
    def extract_clusters(clusters):
        clusters_texts = clusters.strip().split("\n")
        clusters = [c.split("\t")[1] for c in clusters_texts]
        reasons = [c.split("\t")[-1] for c in clusters_texts]
        new_clusters = []
        for c in clusters:
            c = c.replace("Solution", "")
            c = ast.literal_eval(c)
            new_clusters.append(c)
        return new_clusters, reasons

    origin_data = read_jsonl(origin_file)
    responses = read_jsonl(response_file)
    # merge response to origin data
    for line in responses:
        idx = line["metadata"]["data_idx"]
        origin_line = origin_data[idx]
        origin_line["cluster_response"] = line["response"]

    pattern = r'^cluster\d+\t\[[^\]]*\]\t.+$'

    for i, line in enumerate(responses):
        origin_line = origin_data[line["metadata"]["data_idx"]]
        clustersinfo = line["response"].encode().decode('unicode-escape')
        cleaninfo = ""
        numcluster = 0
        for info in clustersinfo.split("\n"):
            if re.match(pattern, info):
                numcluster += 1
                cleaninfo = cleaninfo + info + "\n"
        cleaninfo = cleaninfo.strip()
        try:
            origin_line["clusters"] = extract_clusters(cleaninfo)
        except:
            origin_line["clusters"] = None
        origin_line["number_of_clusters"] = numcluster

        if origin_line["clusters"] is None:
            continue
        clusters, reasons = origin_line["clusters"]
        cluster_ids = [None for _ in range(len(origin_line["split_solutions"]))]
        for cluster_id, cluster in enumerate(clusters):
            for cluster_idx in cluster:
                if cluster_idx-1 >= len(cluster_ids) or cluster_idx-1 < 0:
                    continue
                cluster_ids[cluster_idx-1] = cluster_id
        origin_line["cluster_ids"] = cluster_ids

    write_jsonl(output_file, origin_data)


if __name__ == "__main__":
    fire.Fire()
