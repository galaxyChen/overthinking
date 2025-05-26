## Do NOT Think That Much for 2+3=? On the Overthinking of o1-Like LLMs

本仓库为论文[Do NOT Think That Much for 2+3=? On the Overthinking of o1-Like LLMs](https://arxiv.org/abs/2412.21187)的代码开源，包含核心的解答切分功能。



### 环境准备

```bash
pip install -r requirements.txt
```

*注意：antlr4-python3-runtime==4.11.0 是必须项，若不满足可能导致数学评估结果有误*



#### 服务器准备

由于运行过程中需要访问大模型，需要提前配置相关API: `src/api_config.json`

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

其中，`meta-llama/Llama-3.3-70B-Instruct`用于解答切分，`KbsdJames/Omni-Judge`用于数学结果评估，`gpt-4o-mini`用于解答多样性分析。填写时，endpoint为具体模型访问的api（推荐使用`vllm`部署），model为具体模型访问的名字。



### 切分与评估

#### 输入文件

输入文件为jsonl格式，可见`data/debug.jsonl`示例，每一行需要包含如下域：

```json
{
  "problem": "问题",
  "response": "大模型的生成结果",
  "expected_answer": "标准回答"
}
```

#### 切分答案

如果仅需要切分答案，不需要运行后续评估指标的计算，仅需准备`meta-llama/Llama-3.3-70B-Instruct`的服务器。

```bash
cd scripts
bash ./run_split_solution.sh [input_file] [output_file]
```

其中，`input_file`为上述格式的输入文件，`[output_file]`为切分结果输出路径。完成后，输出文件的每一行会多出两个域：

```json
{
  "split_solutions": ["切分的结果"],
  "split_answers": ["每一个切分对应的答案"]
}
```



#### 全流程: 解答切分、数学性能评估、思路聚类以及指标计算

在设置好所有服务器后，运行：

```bash
cd scripts
bash ./run_pipeline.sh [input_file] [output_file] [model]
```

其中，`[input_file]`为上述格式的输入文件，`[output_file]`是最终输出的结果文件，`[model]`为生成该输入的模型，用于加载Tokenizer。

全流程包括如下步骤：

1. 解答切分。将大模型生成的回复切分成独立的解答。切分完成后，每一行会多出两个域：

   ```json
   {
     "split_solutions": ["切分的结果"],
     "split_answers": ["每一个切分对应的答案"]
   }
   ```

   

2. 数学性能评估。对大模型生成的答案进行数学性能的评估。评估完成后，每一行会多出三个域：

   ```json
   {
     "rule_correctness": True/False, //使用规则评估的结果
     "llm_correctness": True/False, //使用大模型评估的结果
     "correct": True/False //综合上述两者的最终结果
   }
   ```

3. 切分解答级别的性能评估。对每一个切分出来的答案进行正确性的判定。评估完成后，每一行会多出一个域：

   ```json
   {
     "solution_correctness": [{"correct": True/False}]
   }
   ```

   分别为每一个切分结果对应的正确性。

4. 解答多样性分析。调用`gpt-4o-mini`进行解答的多样性分析。分析完后，每一行会多出三个域：

   ```json
   {
     "cluster_response": "gpt-4o-mini的多样性分析回复",
     "cluster": "多样性分析解析结果",
     "cluster_ids": "每一个切分结果对应的多样性类别"
   }
   ```

   

5. 合并文件并计算相关指标。完成后，会输出一个最终结果文件，并打印`Outcome Efficiency`和`Process Efficiency`的结果。结果文件格式如下：

   ```json
   {
     "problem": "问题",
     "response": "大模型的生成结果",
     "expected_answer": "标准回答",
     "split_solutions": [
       {
         "solution": "子解答",
         "correct": True/False, //该子解答的正确性
         "cluster": 0 //该子解答所属的思路类
       }
     ],
     "correct": True/False
   }
   ```

   