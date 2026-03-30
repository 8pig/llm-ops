#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent智能体执行引擎 - Python示例
用于测试 LLM Agent 与工具调用的基础框架
"""

import json
import time
from typing import Dict, List, Optional

# ==================== 配置部分 ====================
AGENT_SYSTEM_PROMPT = """
请尽最大努力回答用户的问题。您拥有以下工具可用：

{tools}

请严格按照以下格式进行思考和执行：

【问题】：需要回答的用户输入
【思考】：分析当前情况，决定下一步行动
【动作】：从下列工具中选择一个：[{tool_names}]
【参数】：传递给该工具的输入数据
【反馈】：工具执行后返回的结果
...（上述思考→动作→反馈流程可循环多次）
【结论】：基于所有信息得出最终理解
【回复】：给用户的最终回答

开始处理：

【问题】：{input}
【思考】：{agent_scratchpad}
"""

MAX_ITERATIONS = 5
STOP_TOKENS = ["【回复】:", "###END###", "Final Answer"]


# ==================== 工具定义 ====================

def get_weather(city: str) -> dict:
    """获取天气信息"""
    return {"city": city, "temperature": "25°C", "condition": "晴朗"}


def search_info(query: str) -> str:
    """搜索互联网信息"""
    results = {
        "北京": "中国的首都",
        "天气": "今天是晴天",
        "时间": "当前时间为" + time.strftime("%Y-%m-%d %H:%M:%S")
    }
    return results.get(query, f"未找到关于{query}的信息")


def calculate_expr(expr: str) -> float:
    """计算数学表达式"""
    try:
        # 注意：生产环境请使用更安全的方式评估表达式
        result = eval(expr, {"__builtins__": None}, {})
        return {"expression": expr, "result": result}
    except Exception as e:
        return {"expression": expr, "error": str(e)}


TOOLS_REGISTRY = {
    "get_weather": get_weather,
    "search_info": search_info,
    "calculate_expr": calculate_expr
}

TOOL_DESCRIPTIONS = """
可用的工具列表：
- get_weather(city): 查询指定城市的天气情况
- search_info(query): 搜索特定关键词的信息
- calculate_expr(expr): 计算简单的数学表达式
"""

TOOL_NAMES = list(TOOLS_REGISTRY.keys())


# ==================== Agent核心类 ====================

class SimpleAgent:
    def __init__(self, model_client=None):
        self.model_client = model_client or MockModelClient()
        self.iteration = 0
        self.history = []

    def build_prompt(self, input_query: str, scratchpad: str = "") -> str:
        """构建完整的Prompt"""
        tools_desc = TOOL_DESCRIPTIONS
        tool_names_str = ", ".join(f'"{t}"' for t in TOOL_NAMES)

        return AGENT_SYSTEM_PROMPT.format(
            tools=tools_desc,
            tool_names=tool_names_str,
            input=input_query,
            agent_scratchpad=scratchpad
        )

    def parse_agent_output(self, output: str) -> tuple:
        """解析Agent输出的格式"""
        response = {
            "thought": "",
            "action": None,
            "action_input": {},
            "conclusion": "",
            "final_answer": ""
        }

        lines = output.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()

            if "【思考】：" in line:
                current_section = "thought"
                response["thought"] = line.split("：", 1)[1]
            elif "【动作】：" in line:
                current_section = "action"
                action_name = line.split("：", 1)[1].strip().strip('"').strip("'")
                response["action"] = action_name
            elif "【参数】：" in line:
                current_section = "parameters"
                try:
                    response["action_input"] = json.loads(line.split("：", 1)[1])
                except:
                    response["action_input"] = {}
            elif "【反馈】：" in line:
                current_section = "feedback"
            elif "【结论】：" in line:
                current_section = "conclusion"
                response["conclusion"] = line.split("：", 1)[1]
            elif "【回复】：" in line:
                current_section = "final_answer"
                response["final_answer"] = line.split("：", 1)[1]
            else:
                pass  # 忽略其他行

        return response

    def execute_action(self, action: str, action_input: dict) -> str:
        """执行指定的工具调用"""
        if action not in TOOLS_REGISTRY:
            return f"错误：未知工具 '{action}'"

        try:
            tool_func = TOOLS_REGISTRY[action]
            result = tool_func(**action_input)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return f"错误：执行失败 - {str(e)}"

    def run(self, query: str) -> str:
        """主执行流程"""
        print("=" * 60)
        print(f"🤖 Agent 启动 - 处理问题：{query}")
        print("=" * 60)

        iteration = 0
        scratchpad = ""
        last_observation = ""

        while iteration < MAX_ITERATIONS:
            iteration += 1
            print(f"\n[第{iteration}次迭代]")

            # 1. 生成Prompt并发送给LLM
            prompt = self.build_prompt(query, scratchpad)
            print(f"📝 Prompt:\n{prompt[:200]}...")

            # 模拟LLM响应（实际使用真实API时替换此部分）
            llm_response = self.model_client.call(prompt)
            print(f"\n💬 Agent响应:\n{llm_response[:300]}...")

            # 2. 解析Agent输出
            parsed = self.parse_agent_output(llm_response)

            # 3. 检查是否已给出最终答案
            if parsed["final_answer"] and len(parsed["final_answer"]) > 20:
                print(f"\n✅ 得到最终答案")
                break

            # 4. 如果选择了动作，执行它
            if parsed["action"]:
                print(f"⚙️  执行操作：{parsed['action']}")

                # 确保action_input是字典
                if isinstance(parsed["action_input"], str):
                    try:
                        action_input = json.loads(parsed["action_input"])
                    except:
                        action_input = parsed["action_input"]
                else:
                    action_input = parsed["action_input"]

                observation = self.execute_action(parsed["action"], action_input)
                print(f"🔍 执行结果：{observation[:150]}...")

                # 更新scratchpad
                scratchpad = f"{scratchpad}\n\n观察结果:{observation}"
            else:
                break

        # 5. 返回最终答案
        final_answer = parsed["final_answer"] if parsed["final_answer"] else "Agent未能给出明确答案"
        print("\n" + "=" * 60)
        print(f"🎯 最终回答：{final_answer}")
        print("=" * 60)

        return final_answer


# ==================== 模拟LLM客户端（测试用） ====================

class MockModelClient:
    """模拟LLM API调用（开发测试阶段用）"""

    def call(self, prompt: str) -> str:
        """根据上下文生成合理的模拟响应"""
        if "get_weather" in prompt.lower() or "天气" in prompt:
            return """
【思考】：用户询问天气，我需要调用weather工具
【动作】：get_weather
【参数】：{"city": "北京"}
【反馈】：等待执行结果...
            """
        elif "计算" in prompt or "math" in prompt.lower():
            return """
【思考】：用户要求计算，我需要调用calculate_expr工具
【动作】：calculate_expr
【参数】：{"expr": "2+3*5"}
【反馈】：等待执行结果...
            """
        elif "最后" in prompt or "回答" in prompt:
            return """
【思考】：已完成工具调用，现在可以总结答案
【结论】：通过天气查询获得了北京的信息
【回复】：北京的天气目前是25°C，晴朗。祝您生活愉快！
            """
        else:
            return """
【思考】：我先尝试搜索一下相关信息
【动作】：search_info
【参数】：{"query": "基本信息"}
【反馈】：等待执行结果...
            """


# ==================== 真正的模型客户端（预留接口） ====================

# class RealModelClient:
#     """真实API调用（接入通义千问/文心一言等）"""
#
#     def call(self, prompt: str) -> str:
#         from dashscope import Generation
#         response = Generation.call(
#             model="qwen-turbo",
#             messages=[{"role": "user", "content": prompt}]
#         )
#         return response.output.choices[0].message.content


# ==================== 主程序入口 ====================

if __name__ == "__main__":
    # 创建Agent实例
    agent = SimpleAgent(model_client=MockModelClient())

    # 测试场景
    test_queries = [
        "北京今天天气怎么样？",
        "帮我算一下 100*50+25",
        "什么是人工智能？",
        "现在是几点钟？"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 70}")
        print(f"🔹 测试用例 {i}/{len(test_queries)}")
        print('=' * 70)
        result = agent.run(query)
        print(f"✅ 测试结果：{result[:50]}...\n")

    print("\n🎉 所有测试完成！")