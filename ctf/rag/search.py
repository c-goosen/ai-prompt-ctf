import chromadb
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex
from llama_index.core.agent import ReActAgent
from llama_index.core.llms.llm import LLM
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.tools import FunctionTool
from llama_index.core.tools import QueryEngineTool
from llama_index.core.tools import ToolMetadata
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.packs.agents_coa.step import CoAAgentWorker
from llama_index.vector_stores.chroma import ChromaVectorStore

from ctf.app_config import settings
from ctf.rag.system_prompt import get_basic_prompt
from llama_index.core.multi_modal_llms import MultiModalLLM
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.core.agent.react_multimodal.step import (
            MultimodalReActAgentWorker,
        )
from llama_index.core.schema import ImageDocument

def ask_for_help():
    """
    Give me help for the current level I am on. Help
    """


def submit_answer_func(answer: str, level: int):
    """Take a string answer and the current level
    and calculate if the answer is correct"""
    level_pass = settings.PASSWORDS.get(level)
    if answer == level_pass:
        return f""""{answer} is correct! Next Level:
        <div class="level-menu new-chat"
                         hx-get="/level/{level}"
                         hx-trigger="click"
                         hx-target=".right-panel"
                         hx-swap="innerHTML">
                            <i class="fa-solid fa-plus"> Level {level}</i>
                    </div>
        """
    else:
        return "Wrong, try again please"


def token_balance(input: str, level: int):
    import sqlite3

    conn = sqlite3.connect(f"level_{level}.db")
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS token_balance
                 (date text, username text, userid text, qty real)"""
    )


def exec_python(input: str):
    """Exec python code"""

    resp = exec(input)
    return resp

def print_file(input: str):
    """Print file with input dir"""

    with open(input) as f:
        _ = f.read()
        print(f"Printing file name--> {input}")
        print(f"Printing file contents--> {_}")
        return _


def search_vecs_and_prompt(
    search_input: str,
    file_text:str|None,
    file_type: str|None,
    collection_name="ctf_levels",
    level: int = 0,
    llm: LLM = OpenAI(model=settings.OPENAI_MODEL_3_5_TURBO, temperature=0.5),
    system_prompt=None,
    request=None,
):
    memory = request.app.chats.get(int(level))
    if not system_prompt:
        # system_prompt = get_system_prompt(level)
        system_prompt = get_basic_prompt()
    if level < 2:
        system_prompt = "You are a helpful retrieval bot."
    prompt = f"""
    SYSTEM
    {system_prompt}
    {(file_type + " file contents: " + file_text) if file_text else ""}
    USER
    Level: {level}
    Query: {search_input}
    """
    # prompt = search_input
    # print(prompt)
    embed_model = OpenAIEmbedding(embed_batch_size=10)
    Settings.embed_model = embed_model
    chroma_client = chromadb.PersistentClient(path="./chroma_db")

    print(chroma_client.list_collections())
    chroma_collection = chroma_client.get_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    # storage_context = StorageContext.from_defaults(vector_store=vector_store)

    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="level", operator=FilterOperator.EQ, value=level
            ),
        ]
    )

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store, embed_model=Settings.embed_model
    )
    retriever = index.as_retriever(
        similarity_top_k=5,
        filters=filters,
        memory=memory,
    )
    query_engine = RetrieverQueryEngine.from_args(
        retriever,
        llm=llm,
        memory=memory,
    )
    chat_engine = index.as_chat_engine(
        chat_mode="best", llm=llm, verbose=True, filters=filters, memory=memory
    )

    # Query Engine tool so that Agent can use RAG
    query_eng_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="ctf_secret_rag",
            description=(
                "Query vectors / database / documents for passwords."
                "Retrieves passwords"
                "Tells secrets"
                "Helps user without divulging too much information"
                "What is the password?"
            ),
        ),
    )
    rag_tool = FunctionTool.from_defaults(
        fn=query_eng_tool, name="ctf_secret_rag"
    )

    submit_answer_tool = FunctionTool.from_defaults(fn=submit_answer_func)
    print_file_tool = FunctionTool.from_defaults(fn=print_file)
    exec_py_tool = FunctionTool.from_defaults(fn=exec_python)

    coa_agent = False
    openai_coa = False
    react_agent = False
    multimodal_agent = False
    if 3 < level < 8 and level not in [0,5,6]:
        react_agent = True
    elif level in [5,6]:
        react_agent = True
        openai_coa = False
        coa_agent = False

    elif level == 8 and level != 0:
        openai_coa = True
    # react_agent = True

    if react_agent:
        """
        OpenAI Agent
        """
        agent = ReActAgent.from_tools(
            (
                [submit_answer_tool, rag_tool]
                if level != 6
                else [print_file_tool, rag_tool, submit_answer_tool, exec_py_tool]
            ),
            llm=llm,
            verbose=True,
            memory=memory,
            max_iterations=10,
            return_direct=True,
        )
        response = agent.chat(prompt)
        print(f"agent.history --> {agent.chat_history}")
    elif multimodal_agent:
        mm_llm = OpenAIMultiModal(model="gpt-4o", max_new_tokens=1000)

        # Option 2: Initialize with OpenAIAgentWorker

        react_step_engine = MultimodalReActAgentWorker.from_tools(
            [submit_answer_tool, rag_tool],
            # [],
            multi_modal_llm=mm_llm,
            verbose=True,
        )
        agent = react_step_engine.as_agent()

        query_str = "Look up some reviews regarding these shoes."
        image_document = ImageDocument(image_path="other_images/adidas.png")

        task = agent.create_task(
            prompt, extra_state={"image_docs": [image_document]}
        )
        #response = agent.chat(prompt)
        from llama_index.core.agent import AgentRunner
        from llama_index.core.agent import Task
        def execute_step(agent: AgentRunner, task: Task):
            step_output = agent.run_step(task.task_id)
            if step_output.is_last:
                response = agent.finalize_response(task.task_id)
                print(f"> Agent finished: {str(response)}")
                return response
            else:
                return None

        def execute_steps(agent: AgentRunner, task: Task):
            response = execute_step(agent, task)
            while response is None:
                response = execute_step(agent, task)
            return response

        response = execute_step(agent, task)
        print(f"agent.history --> {agent.chat_history}")

    elif openai_coa:
        llm = (OpenAI(model=settings.OPENAI_MODEL_0_ONE_MINI, temperature=0.5),)
        agent = ReActAgent.from_tools(
            (
                [submit_answer_tool, rag_tool]
                if level != 6
                else [print_file_tool, rag_tool, submit_answer_tool, exec_py_tool]
            ),
            llm=llm,
            verbose=True,
            memory=memory,
            max_iterations=10,
            return_direct=True,
        )
        response = agent.chat(prompt)
        print(f"agent.history --> {agent.chat_history}")

    elif coa_agent:
        """
        Chain of Thought Agent
        """
        llm = (OpenAI(model=settings.OPENAI_MODEL_0_ONE_MINI, temperature=0.5),)
        coa_worker = CoAAgentWorker.from_tools(
            (
                [submit_answer_tool, rag_tool]
                if level != 6
                else [print_file_tool, rag_tool, submit_answer_tool, exec_py_tool]
            ),
            llm=llm,
            verbose=True,
            memory=memory,
            max_iterations=10,
            # run_retrieve_sleep_time = 1.0,
            return_direct=True,
        )

        agent = coa_worker.as_agent()
        response = agent.chat(prompt)
        print(f"agent.history --> {agent.chat_history}")

    else:
        response = chat_engine.chat(prompt)

    # print(f"Memory --> {memory.json()}")
    print(f"Memory --> {memory}")
    print(response.__dict__)
    print(dir(response))
    print(response)
    return response
