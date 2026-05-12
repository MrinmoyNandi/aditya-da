from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
templete = """
Answer the question below . 

Here is the conversation history : {content}

Question : {question}

Answer :

"""
model = OllamaLLM(model="llama3")
promt = ChatPromptTemplate.from_template(templete)
chain = promt | model

def handle_conversation():
    context=" "
    print("Wwlcomw to the model !!! type 'exit' to quit.")
    while True:
        user_input = input("You : ")
        if user_input.lower() == "exit" :
            break
        result = chain.invoke({"context":context,"question":user_input})
        print("Bot : " , result)
        context += f"\n User : {user_input}\nAI : {result}"

if __name__ == "__main__":
    handle_conversation()
