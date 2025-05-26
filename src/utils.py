import json

def read_json(file):
    with open(file, 'r') as f:
        return json.load(f)
    
def write_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

def read_jsonl(file):
    with open(file, 'r') as f:
        return [json.loads(line) for line in f]
    
def write_jsonl(file, data):
    with open(file, 'w') as f:
        for line in data:
            json.dump(line, f)
            f.write('\n')

def extract_answer_boxed(text):
    if "\\boxed{" not in text:
        return None
    start_idx = text.rfind("\\boxed{")
    answer_text = text[start_idx + len("\\boxed{"):]
    bracket = 1
    idx = 0
    while idx < len(answer_text) and bracket > 0:
        if answer_text[idx] == "{":
            bracket += 1
        if answer_text[idx] == "}":
            bracket -= 1
        idx += 1
    if bracket == 0:
        predicted_answer = answer_text[:idx-1]
    else:
        predicted_answer = None
    return predicted_answer
