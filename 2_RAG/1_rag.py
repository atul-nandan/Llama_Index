# for stage 1
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
# for stage 2 
from llama_index.core import VectorStoreIndex, Settings , StorageContext, load_index_from_storage
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

from workflows import Workflow, Context, step

from dotenv import load_dotenv
import os

load_dotenv()

# ──────────────────────────────────────────────
# STAGE 1: LOAD
# ──────────────────────────────────────────────
print("=" * 25)
print("STAGE 1 — LOAD")
print("=" * 25)
 
# SimpleDirectoryReader auto-detects file types (.txt, .pdf, etc.)
documents = SimpleDirectoryReader("./RAG/data", required_exts=[".txt"], num_files_limit=4).load_data()
print(f"  Loaded {len(documents)} document(s):")
for doc in documents:
    # Metadata includes the source filename
    name = doc.metadata["file_name"]
    print(f"    • {name}  ({len(doc.text)} chars)")
 
# Split each Document into smaller Nodes (chunks)
# chunk_size: max tokens per chunk
# chunk_overlap: tokens shared between adjacent chunks (preserves boundary context)
splitter = SentenceSplitter(chunk_size=256, chunk_overlap=30)
# print(splitter)
nodes = splitter.get_nodes_from_documents(documents)
print(f"\n  Split into {len(nodes)} nodes (chunk_size=256, overlap=30)")
# print(nodes)
for node in nodes:
    print(f"Node id is : {node.id_},  file name is :{ node.metadata["file_name"]}, Text is : {node.text[:100]}, {node}")
    
    
 
# ──────────────────────────────────────────────
# STAGE 2: INDEX
# ──────────────────────────────────────────────

 
print("=" * 40)
print("STAGE 2 — INDEX (embed + store)")
print("=" * 40)
 
# Global settings — applied to all LlamaIndex operations
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)
Settings.llm = Groq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY")
)
 
# Build the vector index: embeds every node and stores (vector, text, metadata)
# This makes one embedding API call per node — cache or persist to avoid repeating.
# index = VectorStoreIndex.from_documents(documents, show_progress=True)
# print("  VectorStoreIndex built successfully.")
 
# Persist/Save to disk so we don't re-embed on next run
STORAGE_DIR = "./rag_storage"
# index.storage_context.persist(persist_dir=STORAGE_DIR)
# print(f"  Index persisted to {STORAGE_DIR}/\n")
 
# ── To reload from disk next time, instead of re-embedding: 
storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
index = load_index_from_storage(storage_context)
print(f"Successfully Loaded the data from {STORAGE_DIR}")


# ──────────────────────────────────────────────
# STAGE 3: RETRIEVE
# ──────────────────────────────────────────────
 
print("=" * 40)
print("STAGE 3 — RETRIEVE (semantic search)")
print("=" * 40)
 
QUERY = "How many trophies Ms Dhoni has won ?"
 
# The retriever embeds the query then returns the top-k most similar nodes
# We can apply "filters" also : 👉 Only search inside specific data
retriever = index.as_retriever( similarity_top_k=3,  filters=MetadataFilters(
        filters=[
            ExactMatchFilter(key="file_name", value="msdhoni.txt")
        ]
    ))
retrieved_nodes = retriever.retrieve(QUERY)

 
print(f"  Query: \"{QUERY}\"")
print(f"  Top {len(retrieved_nodes)} retrieved chunks:\n")
for i, node_with_score in enumerate(retrieved_nodes, 1):
    score = node_with_score.score
    text_preview = node_with_score.node.text.replace("\n", " ")
    source = node_with_score.node.metadata.get("file_name", "?")
    print(f"  [{i}] score={score:.4f}  source={source}")
    print(f"      \"{text_preview}…\"\n")
 

 
    
# ──────────────────────────────────────────────
# STAGE 4: GENERATE (RAG query)
# ──────────────────────────────────────────────
 
print("=" * 40)
print("STAGE 4 — GENERATE (augmented answer)")
print("=" * 40)
 
# QueryEngine = retriever + prompt builder + LLM in one call
query_engine = index.as_query_engine(
    similarity_top_k=3,       # how many chunks to inject into context
    response_mode="compact",  # compact: fits chunks into fewest LLM calls
    # we can also add filters to get response from a particular source/ file 
    filters=MetadataFilters(filters=[
        ExactMatchFilter(key="file_name", value="msdhoni.txt")
    ]),
)
 
response = query_engine.query(QUERY)
 
print(f"  Query: \"{QUERY}\"")
print(f"\n  Answer:\n")
print(response)
 
print(f"\n  Grounded in {len(response.source_nodes)} source node(s):")
for src in response.source_nodes:
    print(f" {src.node.metadata.get('file_name', '?')}  "
          f"score={src.score:.4f}")
 
 
# ──────────────────────────────────────────────
# BONUS: Chat mode (multi-turn memory)
# ──────────────────────────────────────────────
 
print("\n" + "=" * 40)
print("BONUS — Chat engine (conversational RAG)")
print("=" * 40)
 
chat_engine = index.as_chat_engine(
    chat_mode="condense_plus_context",   # condenses history + retrieves context
    similarity_top_k=3,
    filters=MetadataFilters(filters=[
        ExactMatchFilter(key="file_name", value="msdhoni.txt")
    ]),
    verbose=True,
)

response1= chat_engine.chat("Whom we are talking about ?")
print(response1)
response2= chat_engine.chat("who is he ?")
print(response2)

 
print("\n[done] RAG pipeline complete.")
 