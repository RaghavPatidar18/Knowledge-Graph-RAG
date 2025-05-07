from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError(" Missing GROQ_API_KEY in environment variables!")

llm = ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.3-70b-versatile")

prompt_template = ChatPromptTemplate.from_template(
    """
    You are a helpful travelling guide assistant that answers questions based on the following knowledge graph content base. 
    Aggregate the fact from the items in the below context:

    {context}

    Now anwser the following question:
    Question: {question}
    Answer in a concise and informative manner considering the context. Do not make assumption.
    And DO NOT reply starting with the unessesary information make it to the point and also in interesting way.
    """
)

def answer_from_kgllm(question: str, context: str) -> str:

    formatted_prompt = prompt_template.format_messages(
        context=context,
        question=question
    )
    response = llm.invoke(formatted_prompt)
    return response.content