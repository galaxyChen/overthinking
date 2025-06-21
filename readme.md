# Do NOT Think That Much for 2+3=? On the Overthinking of Long Reasoning Models

[English](#do-not-think-that-much-for-23-on-the-overthinking-of-o1-like-llms) | [中文](readme_zh.md) | [Paper](https://arxiv.org/abs/2412.21187)

This repository contains the official implementation for the paper **"Do NOT Think That Much for 2+3=? On the Overthinking of Long Reasoning Models"**.

## 📰 News

- **June 2025**: Code release with full evaluation pipeline
- **May 2025**: Paper accepted at ICML2025

## 🎯 Overview

This project addresses the phenomenon of "overthinking" in long reasoning models. The core functionality includes:

- **Solution Splitting**: Automatically segmenting LLM responses into solutions
- **Mathematical Performance Evaluation**: Assessing correctness using both rule-based and LLM-based evaluation
- **Solution-Level Analysis**: Evaluating correctness of each solution
- **Diversity Analysis**: Clustering solutions to analyze reasoning diversity
- **Efficiency Metrics**: Computing Outcome Efficiency and Process Efficiency metrics

## 🚀 Quick Start

### Environment Setup

```bash
pip install -r requirements.txt
```

**Note:** `antlr4-python3-runtime==4.11.0` is required for accurate mathematical evaluation results.

### API Configuration

Configure your model APIs in `src/api_config.json`:

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

**Model Usage:**

- `meta-llama/Llama-3.3-70B-Instruct`: Solution splitting
- `KbsdJames/Omni-Judge`: Mathematical evaluation
- `gpt-4o-mini`: Solution diversity analysis

## 📊 Input Format

Input files should be in JSONL format (see `data/debug.jsonl` for examples):

```json
{
  "problem": "Problem statement",
  "response": "LLM generated response",
  "expected_answer": "Expected answer"
}
```

## 🔧 Usage

### Solution Splitting Only

If you only need to split solutions without running full evaluation:

```bash
cd scripts
bash ./run_split_solution.sh [input_file] [output_file]
```

Output will include:

```json
{
  "split_solutions": ["split results"],
  "split_answers": ["answers for each split"]
}
```

### Full Pipeline

Run the complete evaluation pipeline:

```bash
cd scripts
bash ./run_pipeline.sh [input_file] [output_file] [model]
```

The full pipeline includes:

1. **Solution Splitting**: Segment responses into independent solutions
2. **Mathematical Performance Evaluation**: Assess correctness using rules and LLM evaluation
3. **Solution-Level Evaluation**: Evaluate correctness for each split
4. **Diversity Analysis**: Analyze solution diversity using GPT-4o-mini
5. **Metrics Computation**: Calculate Outcome Efficiency and Process Efficiency

### Individual Components

You can also run individual components:

- **Diversity Analysis**: `bash ./run_diversity.sh`
- **Mathematical Evaluation**: `bash ./run_math_eval.sh`
- **Solution-Level Evaluation**: `bash ./run_solution_level_eval.sh`

## 📈 Output Metrics

The system computes two key efficiency metrics:

- **Outcome Efficiency**: Measures how efficiently the model reaches correct solutions
- **Process Efficiency**: Measures the diversity of reasoning approaches used

## 📁 Project Structure

```
├── data/                    # Data files for and temporary outputs
├── scripts/                 # Execution scripts
├── src/                     # Core implementation
│   ├── prompts/            # LLM prompts for various tasks
│   ├── split_solution.py   # Solution splitting logic
│   ├── compute_metrics.py  # Efficiency metrics computation
│   └── ...
└── requirements.txt        # Python dependencies
```

## 🤝 Citation

If you find this work useful, please cite our paper:

```bibtex
@article{chen2024not,
  title={Do not think that much for 2+ 3=? on the overthinking of o1-like llms},
  author={Chen, Xingyu and Xu, Jiahao and Liang, Tian and He, Zhiwei and Pang, Jianhui and Yu, Dian and Song, Linfeng and Liu, Qiuzhi and Zhou, Mengfei and Zhang, Zhuosheng and others},
  journal={arXiv preprint arXiv:2412.21187},
  year={2024}
}
```
