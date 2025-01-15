from dotenv import load_dotenv
load_dotenv()

from src.prompts.sofia_prompt import SOFIA_SYSTEM_PROMPT

# import asyncio
# user_id = 1234
# user_message = "Hello"
# response = asyncio.run(agent.generate_response(user_message, user_id))
# print(response)

import os, json
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langgraph.graph import MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition

# from langchain.globals import set_debug, set_verbose
# set_debug(True)
# set_verbose(True)

from langchain_core.tools import tool #, InjectedToolArg
from langchain_core.runnables.config import RunnableConfig

IMAGES = json.load(open("data/image_metadata.json"))

@tool
def send_message(message: str) -> str:  # user_id: InjectedToolArg
    """
    Send a message to the user or human (everything else is just internal monologue). Always invoke this tool at the end to actually send message to the user.
    """
    return f"replied: {message}"

@tool
def send_image(config: RunnableConfig) -> str:  # user_id: InjectedToolArg
    """
    Tool that sends an image to the user or human. Only invoke this tool when user demands for an image or photo.
    """
    import random
    from src.instagram_api import InstagramAPI
    api = InstagramAPI()
    user_id = config.get("configurable", {}).get("user_id")
    images = list(IMAGES["categories"]["1"]["images"].values())
    image = images[random.randint(0, len(images)-1)]
    desc, file_id = image["description"], image["fileid"]
    api.send_media_message(user_id, f"https://drive.google.com/uc?export=download&id={file_id}", "image")
    return f"photo of sophia, {desc}"

def create_app(model_config, system_prompt, tools):
    llm = ChatOpenAI(**model_config).bind_tools(tools)
    sys_prompt = [SystemMessage(system_prompt)]

    def chatbot(state: MessagesState):
        response = llm.invoke(sys_prompt + state["messages"])
        return {"messages": response}

    graph = StateGraph(state_schema=MessagesState)
    graph.add_node("chatbot", chatbot)

    graph.add_node("tools", ToolNode(tools=tools))

    graph.add_conditional_edges("chatbot", tools_condition)
    graph.add_edge("tools", "chatbot")  # link tools   -> chatbot
    graph.set_entry_point("chatbot")    # link START   -> chatbot
    graph.set_finish_point("chatbot")   # link chatbot -> END

    memory = MemorySaver()
    app = graph.compile(checkpointer=memory)
    return app

def get_app_config(thread_id, user_id):
    return {"configurable": {"thread_id": thread_id, "user_id": user_id}}

def main():
    from langchain_community.callbacks import get_openai_callback

    def divider(n): print("\n"+"-"*n)

    model_config = dict(
        model = "gpt-4o-mini",  # https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo#gpt-4-turbo-and-gpt-4
        api_key=os.getenv("OPENAI_API_KEY"),
        max_tokens=150,
        temperature=0.7,
    )

    tools = [send_image]
    app = create_app(model_config, SOFIA_SYSTEM_PROMPT, tools)
    # app.get_graph().draw_mermaid_png(output_file_path="graph.png")

    user_id = "1512552969452550"
    config = get_app_config(f"user:{user_id}", user_id)
    # user_messages = ["Hello", "tell me about elon musk", "list his companies", "how old is he?"]

    max_steps = 5
    counter = 0
    with get_openai_callback() as cb:
        while counter < max_steps:
            input_message = [HumanMessage(input("Human: "))]
            output = app.invoke({"messages": input_message}, config)
            output["messages"][-2].pretty_print()  # human
            output["messages"][-1].pretty_print()  # ai
            counter += 1
            # if counter == len(user_messages): break

    divider(80)
    print(cb)

if __name__ == "__main__":
    main()
