# Do NOT Think That Much for 2+3=? On the Overthinking of Long Reasoning Models

[English](readme.md) | [中文](#2-3-不要想太多长推理模型的过度思考问题) | [Paper](https://arxiv.org/abs/2412.21187)

本仓库包含论文 **"Do NOT Think That Much for 2+3=? On the Overthinking of Long Reasoning Models"** 的官方实现。

## 📰 最新动态

- **2025年6月**: 发布完整评估流程代码
- **2025年5月**: 论文被ICML2025接收 

## 🎯 概述

本项目针对长推理模型中的"过度思考"现象进行研究。核心功能包括：

- **解答切分**: 自动将LLM响应分割成独立的解答
- **数学性能评估**: 使用基于规则和基于LLM的方法评估正确性
- **解答级别分析**: 评估每个解答的正确性
- **多样性分析**: 对解答进行聚类以分析推理多样性
- **效率指标**: 计算结果效率和过程效率指标

## 🚀 快速开始

### 环境准备

```bash
pip install -r requirements.txt
```

**注意:** `antlr4-python3-runtime==4.11.0` 是必需的，否则可能导致数学评估结果不准确。

### API配置

在 `src/api_config.json` 中配置您的模型API：

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

**模型用途:**

- `meta-llama/Llama-3.3-70B-Instruct`: 解答切分
- `KbsdJames/Omni-Judge`: 数学评估
- `gpt-4o-mini`: 解答多样性分析

## 📊 输入格式

输入文件应为JSONL格式（参见 `data/debug.jsonl` 示例）：

```json
{
  "problem": "问题描述",
  "response": "LLM生成的响应",
  "expected_answer": "期望答案"
}
```

## 🔧 使用方法

### 仅解答切分

如果只需要切分解答而不运行完整评估：

```bash
cd scripts
bash ./run_split_solution.sh [input_file] [output_file]
```

输出将包含：

```json
{
  "split_solutions": ["切分结果"],
  "split_answers": ["每个切分对应的答案"]
}
```

### 完整流程

运行完整的评估流程：

```bash
cd scripts
bash ./run_pipeline.sh [input_file] [output_file] [model]
```

完整流程包括：

1. **解答切分**: 将响应分割成独立的解答
2. **数学性能评估**: 使用规则和LLM评估正确性
3. **解答级别评估**: 评估每个切分的正确性
4. **多样性分析**: 使用GPT-4o-mini分析解答多样性
5. **指标计算**: 计算结果效率和过程效率

### 独立组件

您也可以运行独立组件：

- **多样性分析**: `bash ./run_diversity.sh`
- **数学评估**: `bash ./run_math_eval.sh`
- **解答级别评估**: `bash ./run_solution_level_eval.sh`

## 📈 输出指标

系统计算两个关键效率指标：

- **结果效率**: 衡量模型达到正确解答的效率
- **过程效率**: 衡量使用的推理方法的多样性

## 📁 项目结构

```
├── data/                    # 数据文件和临时输出
├── scripts/                 # 执行脚本
├── src/                     # 核心实现
│   ├── prompts/            # 各种任务的LLM提示
│   ├── split_solution.py   # 解答切分逻辑
│   ├── compute_metrics.py  # 效率指标计算
│   └── ...
└── requirements.txt        # Python依赖
```

## 🤝 引用

如果您觉得这项工作有用，请引用我们的论文：

```bibtex
@article{chen2024not,
  title={Do not think that much for 2+ 3=? on the overthinking of o1-like llms},
  author={Chen, Xingyu and Xu, Jiahao and Liang, Tian and He, Zhiwei and Pang, Jianhui and Yu, Dian and Song, Linfeng and Liu, Qiuzhi and Zhou, Mengfei and Zhang, Zhuosheng and others},
  journal={arXiv preprint arXiv:2412.21187},
  year={2024}
}
```
