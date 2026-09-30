import os
import json
import re

# 📝 标准答案（人工标注）
GROUND_TRUTH = {
    "02_reentrancy_Attack": {"has_reentrancy": True, "type": "single_function"},
    "02_reentrancy_FixedEtherVault": {"has_reentrancy": False, "type": "none"},
    "02_reentrancy_InsecureEtherVault": {"has_reentrancy": True, "type": "single_function"},
    "03_reentrancy_via_modifier_Attack": {"has_reentrancy": True, "type": "via_modifier"},
    "03_reentrancy_via_modifier_Dependencies": {"has_reentrancy": False, "type": "none"},
    "03_reentrancy_via_modifier_FixedAirdrop": {"has_reentrancy": False, "type": "none"},
    "03_reentrancy_via_modifier_InsecureAirdrop": {"has_reentrancy": True, "type": "via_modifier"},
    "04_cross_function_reentrancy_Attack": {"has_reentrancy": True, "type": "cross_function"},
    "04_cross_function_reentrancy_Dependencies": {"has_reentrancy": False, "type": "none"},
    "04_cross_function_reentrancy_FixedEtherVault": {"has_reentrancy": False, "type": "none"},
    "04_cross_function_reentrancy_InsecureEtherVault": {"has_reentrancy": True, "type": "cross_function"},
}

def parse_json_from_text(text):
    """从大模型的输出中提取 JSON 片段（终极容错版）"""
    try:
        # 去除 Markdown 标记
        text = text.replace("```json", "").replace("```", "").strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception as e:
        print(f"⚠️ JSON 解析失败，尝试正则提取: {e}")
        try:
            # 强行用正则提取关键字段
            has_reentrancy = re.search(r'"has_reentrancy"\s*:\s*(true|false)', text, re.IGNORECASE)
            type_match = re.search(r'"type"\s*:\s*"([^"]+)"', text)
            return {
                "has_reentrancy": has_reentrancy.group(1).lower() == 'true' if has_reentrancy else False,
                "type": type_match.group(1) if type_match else "none"
            }
        except Exception:
            return {"has_reentrancy": False, "type": "none"}
    return None

def evaluate(results_dir):
    tp = fp = tn = fn = 0
    type_correct = 0
    total = 0
    missed = 0

    for name, truth in GROUND_TRUTH.items():
        result_file = os.path.join(results_dir, f"{name}.txt")
        if not os.path.exists(result_file):
            print(f"⚠️ 缺失文件: {result_file}")
            missed += 1
            continue

        with open(result_file, encoding="utf-8") as f:
            text = f.read()

        parsed = parse_json_from_text(text)
        if not parsed:
            print(f"❌ 无法解析 JSON: {name}")
            missed += 1
            continue

        predicted = parsed.get("has_reentrancy", False)
        pred_type = parsed.get("type", "none")

        # 混淆矩阵计数
        if truth["has_reentrancy"] and predicted:
            tp += 1
        elif not truth["has_reentrancy"] and predicted:
            fp += 1
        elif not truth["has_reentrancy"] and not predicted:
            tn += 1
        elif truth["has_reentrancy"] and not predicted:
            fn += 1

        # 类型判断准确率
        if pred_type == truth["type"]:
            type_correct += 1
        total += 1

    # 计算指标
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    type_acc = type_correct / total if total > 0 else 0

    print("\n" + "="*40)
    print("📊 评估结果汇总")
    print("="*40)
    print(f"正确识别的重入漏洞 (TP): {tp}")
    print(f"误报 (FP): {fp}")
    print(f"正确排除了无漏洞合约 (TN): {tn}")
    print(f"漏报 (FN): {fn}")
    print(f"缺失结果文件: {missed}")
    print("-" * 40)
    print(f"精确率 Precision: {precision:.2f}")
    print(f"召回率 Recall: {recall:.2f}")
    print(f"F1 分数: {f1:.2f}")
    print(f"漏洞类型判断准确率: {type_acc:.2f}")
    print("="*40)

if __name__ == "__main__":
    # 评估结合 Slither 后的结果
    evaluate("results/with_slither")