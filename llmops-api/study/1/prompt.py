from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder

prompt = PromptTemplate.from_template("讲一个{subject}的冷笑话")

print(prompt.format(subject="前端"))
print(prompt.invoke({"subject": "前端"}).to_json())
print(prompt.invoke({"subject": "前端"}).to_string())
print(prompt.invoke({"subject": "前端"}).to_messages())



chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个 法律的AI智能助手, 你叫{aiName}"),
    MessagesPlaceholder("chat_history"),
    ("human", "{question}")
])

chat_prompt_value = chat_prompt.invoke({
    "aiName": "法律小助手",
    "chat_history": [],
    "question": "请给我一个法律的例子"
})
print(chat_prompt_value.to_json())
print(chat_prompt_value.to_string())
print(chat_prompt_value.to_messages())
