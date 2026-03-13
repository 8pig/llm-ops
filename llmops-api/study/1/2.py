from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

# 定义各个子模板
instruction_prompt = PromptTemplate.from_template("你正在模拟{person}")
example_prompt = PromptTemplate.from_template("""下面是一个交互例子: 
Q: {example_q}
A: {example_a}

""")
start_prompt = PromptTemplate.from_template("""现在你是一个真实的人，请回答用户的问题
Q: {input}

""")

# 方法 A: 直接在主模板中组合
full_template = PromptTemplate.from_template("""
{instruction}

{example}

{start}
""")


# 使用时手动组合
def create_final_prompt(person, example_q, example_a, input):
    instruction = instruction_prompt.format(person=person)
    example = example_prompt.format(example_q=example_q, example_a=example_a)
    start = start_prompt.format(input=input)

    return full_template.format(
        instruction=instruction,
        example=example,
        start=start
    )


# 使用
prompt = create_final_prompt(
    person="雷军",
    example_q="你最喜欢的汽车是什么",
    example_a="小米su7",
    input="你最喜欢什么手机"
)
print(prompt)
