import hashlib
import os
import re

from dotenv import load_dotenv
from fastembed import TextEmbedding
from groq import Groq
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

load_dotenv()

COLLECTION = "aau_knowledge_v4"
VECTOR_SIZE = 384
DEFAULT_RETRIEVAL_LIMIT = 3
DEFAULT_SCORE_THRESHOLD = 0.35

SYSTEM_PROMPT = """You are a helpful assistant for Al Ain University (AAU) in the UAE. Answer questions directly using the AAU information below.

EXAMPLE of a GOOD response:
User: What programs does AAU offer?
Assistant: AAU offers programs across several colleges:
- College of Engineering: Computer Science, Software Engineering, Cybersecurity, AI & Robotics
- College of Business: BBA, MBA, DBA
- College of Pharmacy: BSc Pharmacy, MSc Clinical Pharmacy
Contact AAU at +800-22864 for more details.

EXAMPLE of a BAD response (NEVER do this):
"Based on the provided context, AAU offers..." FORBIDDEN
"According to the information, AAU has..." FORBIDDEN
"The context mentions that..." FORBIDDEN

Rules:
- Answer directly as if you work at AAU. Never reference any "context" or "information provided".
- Answer only the user's specific question. Do not list unrelated facilities, services, or policies.
- Keep answers concise. Use 2-5 bullets for lists unless the user asks for full details.
- Use bullet points for lists.
- If unsure, say: "Please contact AAU at +800-22864 or visit www.aau.ac.ae."

AAU Information:
{context}"""


class RAGPipeline:
    def __init__(self):
        self.kb_path = os.path.join(os.path.dirname(__file__), "data", "aau_knowledge_base.txt")
        self.kb_hash = self._file_sha256(self.kb_path)
        self.retrieval_limit = int(os.getenv("RAG_RETRIEVAL_LIMIT", DEFAULT_RETRIEVAL_LIMIT))
        self.score_threshold = float(os.getenv("RAG_SCORE_THRESHOLD", DEFAULT_SCORE_THRESHOLD))

        print("Loading embedding model...")
        self.encoder = TextEmbedding("BAAI/bge-small-en-v1.5")

        print("Connecting to Qdrant Cloud...")
        self.qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        self._init_collection()

        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        print("RAG Pipeline ready.")

    def _file_sha256(self, path: str) -> str:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def _init_collection(self):
        existing = [c.name for c in self.qdrant.get_collections().collections]
        needs_rebuild = COLLECTION not in existing

        if not needs_rebuild:
            # Rebuild when metadata is missing or the local knowledge base changed.
            sample = self.qdrant.scroll(COLLECTION, limit=1)[0]
            payload = sample[0].payload if sample else {}
            if (
                not payload
                or "section" not in payload
                or payload.get("kb_hash") != self.kb_hash
            ):
                print("Knowledge base changed or schema upgraded; rebuilding collection...")
                self.qdrant.delete_collection(COLLECTION)
                needs_rebuild = True
            else:
                print(f"Qdrant ready: {self.qdrant.count(COLLECTION).count} vectors loaded")

        if needs_rebuild:
            self.qdrant.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            self._index_documents()

    def _index_documents(self):
        with open(self.kb_path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks, sections = self._chunk_text(text)
        print(f"Indexing {len(chunks)} chunks...")

        embeddings = [e.tolist() for e in self.encoder.embed(chunks)]

        points = [
            PointStruct(
                id=i,
                vector=emb,
                payload={
                    "text": chunk,
                    "section": section,
                    "chunk_id": i,
                    "kb_hash": self.kb_hash,
                },
            )
            for i, (chunk, emb, section) in enumerate(zip(chunks, embeddings, sections))
        ]
        self.qdrant.upsert(collection_name=COLLECTION, points=points)
        print("Indexing complete.")

    def _chunk_text(self, text: str):
        chunks, section_labels = [], []
        raw_sections = text.split("== SECTION:")

        for raw in raw_sections:
            raw = raw.strip()
            if not raw:
                continue

            lines = raw.split("\n")
            title = lines[0].replace("==", "").strip()
            paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]

            current = ""
            for para in paragraphs:
                if current and self._is_subsection_heading(para):
                    chunks.append(current)
                    section_labels.append(self._chunk_label(title, current))
                    current = ""

                candidate = (current + "\n\n" + para).strip() if current else para
                if len(candidate) <= 700:
                    current = candidate
                else:
                    if len(current) > 50:
                        chunks.append(current)
                        section_labels.append(self._chunk_label(title, current))
                    current = para

            if len(current) > 50:
                chunks.append(current)
                section_labels.append(self._chunk_label(title, current))

        return chunks, section_labels

    def _is_subsection_heading(self, paragraph: str) -> bool:
        first_line = paragraph.splitlines()[0].strip()
        return bool(first_line and first_line.endswith(":") and not first_line.startswith("-"))

    def _chunk_label(self, section_title: str, chunk: str) -> str:
        first_line = chunk.splitlines()[0].strip()
        if self._is_subsection_heading(first_line):
            return first_line.rstrip(":")
        return section_title

    def query(self, question: str, history: list | None = None) -> dict:
        history = history or []
        q_embedding = list(self.encoder.embed([question]))[0].tolist()

        results = self.qdrant.search(
            collection_name=COLLECTION,
            query_vector=q_embedding,
            limit=self.retrieval_limit,
            score_threshold=self.score_threshold,
        )

        if not results:
            return {
                "answer": "Please contact AAU at +800-22864 or visit www.aau.ac.ae.",
                "sources": [],
            }

        context_docs = [r.payload["text"] for r in results]
        sections = [r.payload.get("section", "") for r in results]
        context = "\n\n---\n\n".join(context_docs)

        messages = [{"role": "system", "content": SYSTEM_PROMPT.format(context=context)}]
        for msg in history[-6:]:
            messages.append(msg)
        messages.append({"role": "user", "content": question})

        response = self.groq.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=messages,
            max_tokens=600,
            temperature=0,
        )

        answer = self._clean_answer(response.choices[0].message.content)
        sources = self._get_sources(sections)
        return {"answer": answer, "sources": sources}

    def _clean_answer(self, text: str) -> str:
        # Remove any sentence that exposes retrieval internals to the user.
        text = re.sub(r'[^.!?\n]*\bcontext\b[^.!?\n]*[.!?]?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(
            r'(based on|according to)\s+(the\s+)?(provided\s+)?\w+[,.]?\s*',
            '',
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r'However,\s+it\s+does\s+mention\s+that:?\s*', '', text, flags=re.IGNORECASE)
        text = text.strip()
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        return text

    def _get_sources(self, sections: list[str]) -> list[str]:
        seen, result = set(), []
        for s in sections:
            if s and s not in seen:
                seen.add(s)
                result.append(s)
            if len(result) >= 3:
                break
        return result
