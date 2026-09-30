import os
import glob
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
)

MODEL = os.getenv("LLM_MODEL", "glm-4-flash")

def get_slither_summary(contract_path):
    """尝试读取对应合约的 Slither JSON 结果并格式化为摘要"""
    # 这里我们需要建立合约路径和 Slither json 文件路径的映射
    # 假设你手动跑 Slither 时生成的 json 格式是 data/slither/04_fixed.json
    # 这里做个简单的映射，如果是固定合约，可以直接写死路径，或者用文件名匹配
    json_path = None
    
    # 根据合约名映射到对应的 Slither JSON (这里举例匹配 04_fixed)
    if "FixedEtherVault" in contract_path and "04_cross_function" in contract_path:
        json_path = "data/slither/04_fixed.json"
    # 如果是要跑其他合约，可以继续添加映射，或者写一个 glob 查找
    
    if json_path and os.path.exists(json_path):
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            
            detectors = data.get("results", {}).get("detectors", [])
            reentrancy_findings = [d for d in detectors if "reentrancy" in d.get("check", "")]
            
            if not reentrancy_findings:
                return "Slither 静态分析结果：未检测到重入漏洞。"
            
            lines = ["Slither 检测到以下重入相关风险："]
            for i, d in enumerate(reentrancy_findings, 1):
                lines.append(f"[{i}] {d.get('check')} - {d.get('description', '').strip()}")
            return "\n".join(lines)
        except Exception as e:
            return f"读取 Slither 结果出错: {e}"
    else:
        return "未提供该合约的 Slither 静态分析结果。"

def analyze(contract_path, prompt_path, output_path):
    with open(contract_path, encoding="utf-8") as f:
        code = f.read()

    with open(prompt_path, encoding="utf-8") as f:
        prompt_template = f.read()

    # 1. 获取 Slither 摘要
    slither_summary = get_slither_summary(contract_path)
    
    # 2. 替换 Prompt 中的占位符（使用 replace 避免花括号报错）
    prompt = prompt_template.replace("{contract_code}", code)
    prompt = prompt.replace("{slither_summary}", slither_summary)

    # 3. 调用大模型
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content

    # 4. 保存结果
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"Done: {output_path}")

if __name__ == "__main__":
    contracts = glob.glob("data/contracts/**/*.sol", recursive=True)
    print(f"找到 {len(contracts)} 个合约。开始分析...")
    
    for c in contracts:
        name = os.path.basename(os.path.dirname(c)) + "_" + os.path.basename(c).replace(".sol", "")
        
        # ⚠️ 输出目录改成了 results/with_slither/
        out = f"results/with_slither/{name}.txt"
        try:
            analyze(c, "prompts/reentrancy_prompt.txt", out)
        except Exception as e:
            print(f"分析 {c} 时出错: {e}")