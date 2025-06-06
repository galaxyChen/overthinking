## Do NOT Think That Much for 2+3=? On the Overthinking of o1-Like LLMs

This repository contains the code implementation for the paper [Do NOT Think That Much for 2+3=? On the Overthinking of o1-Like LLMs](https://arxiv.org/abs/2412.21187), including the core solution splitting functionality.

### Environment Setup

```bash
pip install -r requirements.txt
```

*Note: antlr4-python3-runtime==4.11.0 is mandatory. Failure to meet this requirement may lead to incorrect mathematical evaluation results.*

#### Server Preparation

Since the process involves accessing large language models, you need to configure the relevant APIs in advance: `src/api_config.json`

```json
{
    "gpt-4o-mini": [
        {
            "endpoint": "",
            "model": "gpt-4o-mini",
            "api_key": "openai"
        }
    ],
    "KbsdJames/Omni-Judge": [
        {
            "endpoint": "http://localhost:8000",
            "model": "KbsdJames/Omni-Judge",
            "api_key": "vllm"
        }
    ],
    "meta-llama/Llama-3.3-70B-Instruct": [
        {
            "endpoint": "http://localhost:8000",
            "model": "meta-llama/Llama-3.3-70B-Instruct",
            "api_key": "vllm"
        }
    ]
}
```

Here, `meta-llama/Llama-3.3-70B-Instruct` is used for solution splitting, `KbsdJames/Omni-Judge` for mathematical result evaluation, and `gpt-4o-mini` for solution diversity analysis. When filling in the configuration, `endpoint` refers to the API for accessing the specific model (recommended to deploy using `vllm`), and `model` is the name used to access the specific model.

### Splitting and Evaluation

#### Input File

The input file should be in JSONL format. See `data/debug.jsonl` for an example. Each line must contain the following fields:

```json
{
  "problem": "Problem statement",
  "response": "LLM-generated response",
  "expected_answer": "Standard answer"
}
```

#### Solution Splitting

If you only need to split the solutions without running subsequent evaluation metrics, you only need to prepare the server for `meta-llama/Llama-3.3-70B-Instruct`.

```bash
cd scripts
bash ./run_split_solution.sh [input_file] [output_file]
```

Here, `input_file` is the input file in the format described above, and `[output_file]` is the output path for the split results. Upon completion, each line in the output file will include two additional fields:

```json
{
  "split_solutions": ["Split results"],
  "split_answers": ["Answers corresponding to each split"]
}
```

#### Full Pipeline: Solution Splitting, Mathematical Performance Evaluation, Solution Clustering, and Metric Calculation

After setting up all servers, run:

```bash
cd scripts
bash ./run_pipeline.sh [input_file] [output_file] [model]
```

Here, `[input_file]` is the input file in the format described above, `[output_file]` is the final output file, and `[model]` is the model used to generate the input (for loading the Tokenizer).

The full pipeline includes the following steps:

1. **Solution Splitting**: Split the LLM-generated response into independent solutions. After splitting, each line will include two additional fields:

   ```json
   {
     "split_solutions": ["Split results"],
     "split_answers": ["Answers corresponding to each split"]
   }
   ```

2. **Mathematical Performance Evaluation**: Evaluate the mathematical performance of the LLM-generated answers. After evaluation, each line will include three additional fields:

   ```json
   {
     "rule_correctness": True/False, // Result from rule-based evaluation
     "llm_correctness": True/False, // Result from LLM-based evaluation
     "correct": True/False // Final result combining the above two
   }
   ```

3. **Split Solution-Level Performance Evaluation**: Evaluate the correctness of each split solution. After evaluation, each line will include one additional field:

   ```json
   {
     "solution_correctness": [{"correct": True/False}]
   }
   ```

   This indicates the correctness of each split solution.

4. **Solution Diversity Analysis**: Use `gpt-4o-mini` to analyze the diversity of solutions. After analysis, each line will include three additional fields:

   ```json
   {
     "cluster_response": "GPT-4o-mini's diversity analysis response",
     "cluster": "Parsed diversity analysis results",
     "cluster_ids": "Diversity category corresponding to each split solution"
   }
   ```

5. **Merge Files and Calculate Metrics**: Upon completion, a final output file will be generated, and the results for `Outcome Efficiency` and `Process Efficiency` will be printed. The output file format is as follows:

   ```json
   {
     "problem": "Problem statement",
     "response": "LLM-generated response",
     "expected_answer": "Standard answer",
     "split_solutions": [
       {
         "solution": "Sub-solution",
         "correct": True/False, // Correctness of this sub-solution
         "cluster": 0 // Thought cluster this sub-solution belongs to
       }
     ],
     "correct": True/False
   }
   ```
