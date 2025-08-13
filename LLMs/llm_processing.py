import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def process_with_llm(prompt_template: str, user_input: str, api_key: str) -> str:
    os.environ["OPENAI_API_KEY"] = api_key
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_template),
        ("user", user_input)
    ])

    output_parser = StrOutputParser()

    chain = prompt | llm | output_parser

    response = chain.invoke({"user_input": user_input})
    return response


