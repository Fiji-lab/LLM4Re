LLM4Re：基于LLM的智能合约重入漏洞分析实验

一、实验目的
利用大语言模型（LLM）分析智能合约代码，探索如何结合静态分析工具（Slither）与Prompt Engineering，提升重入漏洞检测的准确性。

二、实验环境
- Python 3.11
- Slither (静态分析工具)
- 智谱 AI (glm-4-flash 模型)
- 数据集：solidity-security-by-example (02-04重入漏洞样例)

三、实验方案对比
1. 基线组：原始代码 + 基础 Prompt。
2. 优化组：代码裁剪 + JSON 格式化 Prompt。
3. 进阶组：优化组 + Slither 静态分析摘要作为上下文。

四、核心评估指标 (人工标注对比)
| 实验组别 | Precision (精确率) | Recall (召回率) | F1 分数 | 误报数 (FP) |
| :--- | :---: | :---: | :---: | :---: |
| 优化组 (无Slither) | 0.75 | 1.00 | 0.86 | 2 |
| 进阶组 (结合 Slither) |0.86 | 1.00 | 0.92 | 1 |

注：Recall 为 1.00 说明无漏报，成功发现了所有真实漏洞；引入 Slither 后误报减少，Precision 明显提升。

五、如何运行
1. 安装依赖：`pip install -r requirements.txt`
2. 在 `.env` 中配置 API Key（参考 `.env.example`）
3. 运行分析：`python scripts/run_llm.py`
4. 运行评估：`python scripts/evaluate.py`

六、结论与不足
纯 LLM 存在一定幻觉（误报），引入 Slither 等静态分析工具作为上下文能有效提升精确率。未来可探索多合约调用图分析。
