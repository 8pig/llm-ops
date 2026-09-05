from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic.v1 import BaseModel, Field


class Joke(BaseModel):
    joke: str = Field(default="", description="回答用户的冷笑话")
    punchline: str = Field(default="", description="冷笑话的笑点")



parser = JsonOutputParser(pydantic_object=Joke)

prompt = ChatPromptTemplate.from_template("请根据用户的提问进行回答 \n {format_instructions}\n {query}").partial(format_instructions=parser.get_format_instructions())

print(prompt.format(query="讲一个程序员的冷笑话"))