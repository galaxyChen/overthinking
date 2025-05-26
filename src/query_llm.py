import asyncio
from openai import AsyncOpenAI
import argparse
from tqdm import tqdm
import os
import random
import json
from utils import read_jsonl, read_json

clients = []


async def send_request(line, semaphore, write_lock, outf, progress_bar, is_completion):
    if "max_length" not in line:
        max_length = 4096
    else:
        max_length = line["max_length"]
    
    if "temperature" not in line:
        temperature = 0.6
    else:
        temperature = line["temperature"]

    if "top_p" not in line:
        top_p = 0.95
    else:
        top_p = line["top_p"]
    
    if is_completion:
        prompt = line["prompt"]
    else:
        messages = line["messages"]
    while True:
        async with semaphore:
            client, model = random.choice(clients)

            parameters = {
                "model": model,
                "temperature": temperature,
                "max_tokens": max_length,
                "top_p": top_p
            }
            try:
                if is_completion:
                    completion = await client.completions.create(
                        prompt=prompt,
                        timeout=3600,
                        **parameters
                    )
                    response = completion.choices[0].text.strip()
                else:
                    completion = await client.chat.completions.create(messages=messages, timeout=3600, **parameters)
                    response = completion.choices[0].message.content
                line["response"] = response
                async with write_lock:
                    outf.write(json.dumps(line))
                    outf.write("\n")
                    outf.flush()
                progress_bar.update(1)
                return response

            except Exception as e:
                # retry after a short delay
                print(f"Error: {e}, retrying...")
                await asyncio.sleep(10)


async def main(args):
    # Setting up OpenAI clients
    model = args.model
    pwd = os.path.dirname(os.path.abspath(__file__))
    config = read_json(f"{pwd}/api_config.json")
    assert model in config, f"Model {model} not found in api_config.json"
    for url in config[model]:
        clients.append((AsyncOpenAI(
            base_url=f"{url['endpoint']}/v1",
            api_key=url['api_key']
        ), url['model']))

    # load data
    data = read_jsonl(args.input_file)
    for idx, line in enumerate(data):
        line["request_id"] = idx

    if os.path.exists(args.output_file):
        existing_data = read_jsonl(args.output_file)
        finished_idx = set([line["request_id"] for line in existing_data])
        print("Found existing data, will skip these examples ...")
        print("Skipping", len(finished_idx), "examples")
        data = [line for line in data if line["request_id"] not in finished_idx]
        outf = open(args.output_file, "a")
    else:
        outf = open(args.output_file, "w")
    write_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(args.bs)

    print(f"Processing {len(data)} examples ...")
    tasks = []
    progress_bar = tqdm(total=len(data))
    is_completion = args.completion
    for idx, line in enumerate(data):
        tasks.append(send_request(line, semaphore, write_lock, outf, progress_bar, is_completion))
    await asyncio.gather(*tasks)
            

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("--input_file", type=str, required=True)
arg_parser.add_argument("--output_file", type=str, required=True)
arg_parser.add_argument("--bs", type=int, required=False, default=128, help="Batch size for all server")
arg_parser.add_argument("--model", type=str, required=False, default="meta-llama/Llama-3.3-70B-Instruct")
arg_parser.add_argument("--completion", type=bool, required=False, default=False, help="Whether to use completion endpoint or chat endpoint")
args = arg_parser.parse_args()
asyncio.run(main(args))
