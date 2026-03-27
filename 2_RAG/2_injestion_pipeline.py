# for stage 1
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
# for stage 2
from llama_index.core import VectorStoreIndex, Settings, StorageContext, load_index_from_storage
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.extractors import TitleExtractor, KeywordExtractor, SummaryExtractor
from llama_index.core.schema import MetadataMode
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

# ── Constants 
CHUNK_SIZE   = 512
CHUNK_OVERLAP = 64
PERSIST_DIR  = "./storage"

# ── Global settings 
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)
Settings.llm = Groq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY")
)


# --------------------------------------
# STAGE 1: LOAD
# --------------------------------------
def load_documents():
    print("=" * 25)
    print("STAGE 1 — LOAD")
    print("=" * 25)

    # SimpleDirectoryReader auto-detects file types (.txt, .pdf, etc.)
    documents = SimpleDirectoryReader("./data", required_exts=[".txt"], num_files_limit=4).load_data()
    print(f"  Loaded {len(documents)} document(s):")
    for doc in documents:
        # Metadata includes the source filename
        name = doc.metadata["file_name"]
        print(f"    • {name}  ({len(doc.text)} chars)")

    return documents


# --------------------------------------
# STAGE 2: Pipeline
# --------------------------------------
def run_ingestion_pipeline(documents):
    """
    IngestionPipeline chains transformations in order:
      SentenceSplitter → splits docs into overlapping chunks (Nodes)
      TitleExtractor   → infers a title for each chunk (metadata)
      KeywordExtractor → extracts keywords for each chunk (metadata)
      HuggingFaceEmbed → converts each chunk to a dense vector

      The pipeline:
        - Handles deduplication automatically (via document hash cache)
        - Can be run incrementally (only new/changed docs are re-processed)
    """
    print("=" * 40)
    print("STAGE 2 — Injestion-Pipeline (split + embed + store)")
    print("=" * 40)

    print("\n⚙️  Running ingestion pipeline...")

    pipeline = IngestionPipeline(
        transformations=[
            # 1. Split text into overlapping sentence-aware chunks
            SentenceSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
            ),
            # 2. Auto-extract a descriptive title for each node
            TitleExtractor(
                nodes=5,           # Look at first 5 nodes for title generation
                metadata_mode=MetadataMode.EMBED,
            ),
            # 3. Extract relevant keywords per node
            KeywordExtractor(
                keywords=5,        # Up to 5 keywords per chunk
                metadata_mode=MetadataMode.EMBED,
            ),
            # 4. Embed each chunk into a vector
            Settings.embed_model,
        ]
    )

    nodes = pipeline.run(documents=documents, show_progress=True)

    for node in nodes:
        print(node.metadata)
    # print(f"  Pipeline produced {len(nodes)} node(s)")
    # for node in nodes:
    #     print(f"    • Node {node.node_id[:8]}…  "
    #           f"keywords={node.metadata.get('excerpt_keywords', 'n/a')}")
    return nodes

# --------------------------------------
# STAGE 3: BUILD INDEX & PERSIST
# --------------------------------------
def build_and_persist_index(nodes):
    print(f"\n💾 Building index and persisting to '{PERSIST_DIR}'...")
    index = VectorStoreIndex(nodes)
    index.storage_context.persist(persist_dir=PERSIST_DIR)

    persisted = list(Path(PERSIST_DIR).glob("*.json"))
    print(f"  Saved {len(persisted)} file(s):")
    for f in persisted:
        print(f"    • {f.name}  ({f.stat().st_size / 1024:.1f} KB)")
    return index


# --------------------------------------
# STAGE 4: RELOAD FROM DISK
# --------------------------------------
def load_index_from_disk():
    print(f"\n🔄 Reloading index from '{PERSIST_DIR}'...")
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)
    print("  Index reloaded successfully.")
    return index


# --------------------------------------
# STAGE 5: QUERY
# --------------------------------------
def query_index(index):
    """
    Creates a query engine with top-3 retrieval.
    The engine:
      1. Embeds the question
      2. Finds the 3 most similar nodes
      3. Passes them + the question to the LLM
      4. Returns a grounded answer
    """
    print("\n🔍 Querying the index...")
    query_engine = index.as_query_engine(similarity_top_k=3)

    questions = [
        "What is RAG and how does it reduce hallucinations?",
        "What tools does LlamaIndex provide for ingestion?",
        "How does deep learning differ from traditional AI?",
    ]

    for q in questions:
        print(f"\n  Q: {q}")
        response = query_engine.query(q)
        print(f"  A: {response}")
        # Show which source nodes were used
        for i, src in enumerate(response.source_nodes, 1):
            print(f"     [source {i}] {src.node_id}  "
                  f"score={src.score:.3f}")


# --------------------------------------
# MAIN
# --------------------------------------
if __name__ == "__main__":
    # Stage 1 — Load
    documents = load_documents()

    # Stage 2 — Ingest (split + embed)
    nodes = run_ingestion_pipeline(documents)

    # Stage 3 — Build index and persist locally
    index = build_and_persist_index(nodes)

    # Stage 4 — Reload from disk (proves persistence works)
    index = load_index_from_disk()

    # Stage 5 — Query
    query_index(index)