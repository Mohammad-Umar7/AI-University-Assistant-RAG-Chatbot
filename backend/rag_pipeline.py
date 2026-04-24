import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

COLLECTION = "aau_knowledge"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 output dimension

SYSTEM_PROMPT = """You are an intelligent AI assistant for Al Ain University (AAU), UAE. Your role is to help students, applicants, and staff find accurate information about AAU.

Use the following retrieved context to answer the question. Be helpful, accurate, and concise. Use bullet points or numbered lists when listing multiple items. Keep answers focused and clear.

If the specific information is not in the provided context, say: "I don't have specific information about that. Please contact AAU directly at +800-22864 or visit www.aau.ac.ae for the most accurate and up-to-date details."

Never fabricate or guess information. Only use what is provided in the context below.

Context:
{context}"""

SOURCE_MAP = {
    "admission": "Admissions",
    "apply": "Admissions",
    "requirement": "Admissions",
    "document": "Admissions",
    "equivalency": "Admissions",
    "program": "Programs & Colleges",
    "college": "Programs & Colleges",
    "bachelor": "Programs & Colleges",
    "master": "Programs & Colleges",
    "phd": "Programs & Colleges",
    "engineering": "Programs & Colleges",
    "pharmacy": "Programs & Colleges",
    "business": "Programs & Colleges",
    "nursing": "Programs & Colleges",
    "dentistry": "Programs & Colleges",
    "semester": "Academic Calendar",
    "calendar": "Academic Calendar",
    "summer": "Academic Calendar",
    "spring": "Academic Calendar",
    "fall": "Academic Calendar",
    "register": "Course Registration",
    "registration": "Course Registration",
    "drop": "Course Registration",
    "moodle": "Course Registration",
    "withdrawal": "Course Registration",
    "grade": "Grading System",
    "gpa": "Grading System",
    "pass": "Grading System",
    "fail": "Grading System",
    "tuition": "Fees",
    "fee": "Fees",
    "aed": "Fees",
    "scholarship": "Scholarships",
    "financial": "Scholarships",
    "campus": "Campus & Facilities",
    "facility": "Campus & Facilities",
    "library": "Campus & Facilities",
    "transport": "Student Services",
    "shuttle": "Student Services",
    "housing": "Student Services",
    "health": "Student Services",
    "club": "Student Services",
    "visa": "International Students",
    "international": "International Students",
    "probation": "Academic Policies",
    "attendance": "Academic Policies",
    "absence": "Academic Policies",
    "makeup": "Academic Policies",
    "exam": "Academic Policies",
    "contact": "Contact Information",
    "phone": "Contact Information",
    "address": "Contact Information",
    "accreditation": "About AAU",
    "ranking": "About AAU",
}


class RAGPipeline:
    def __init__(self):
        print("Loading embedding model...")
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")

        print("Connecting to Qdrant Cloud...")
        self.qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        self._init_collection()

        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        print("RAG Pipeline ready.")

    def _init_collection(self):
        existing = [c.name for c in self.qdrant.get_collections().collections]

        if COLLECTION not in existing:
            print("Creating Qdrant collection...")
            self.qdrant.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            self._index_documents()
        else:
            count = self.qdrant.count(COLLECTION).count
            if count == 0:
                print("Collection empty — indexing documents...")
                self._index_documents()
            else:
                print(f"Qdrant ready: {count} vectors loaded")

    def _index_documents(self):
        kb_path = os.path.join(os.path.dirname(__file__), "data", "aau_knowledge_base.txt")
        with open(kb_path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = self._chunk_text(text)
        print(f"Indexing {len(chunks)} chunks...")

        embeddings = self.encoder.encode(chunks, show_progress_bar=True).tolist()

        points = [
            PointStruct(id=i, vector=emb, payload={"text": chunk})
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]
        self.qdrant.upsert(collection_name=COLLECTION, points=points)
        print("Indexing complete.")

    def _chunk_text(self, text: str) -> list[str]:
        chunks = []
        sections = text.split("== SECTION:")

        for section in sections:
            section = section.strip()
            if not section:
                continue

            paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
            current = ""

            for para in paragraphs:
                candidate = (current + "\n\n" + para).strip() if current else para
                if len(candidate) <= 700:
                    current = candidate
                else:
                    if len(current) > 50:
                        chunks.append(current)
                    current = para

            if len(current) > 50:
                chunks.append(current)

        return chunks

    def query(self, question: str, history: list = []) -> dict:
        q_embedding = self.encoder.encode([question]).tolist()[0]

        results = self.qdrant.search(
            collection_name=COLLECTION,
            query_vector=q_embedding,
            limit=5,
        )

        context_docs = [r.payload["text"] for r in results]
        context = "\n\n---\n\n".join(context_docs)

        messages = [{"role": "system", "content": SYSTEM_PROMPT.format(context=context)}]
        for msg in history[-6:]:
            messages.append(msg)
        messages.append({"role": "user", "content": question})

        response = self.groq.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
            messages=messages,
            max_tokens=1024,
            temperature=0.2,
        )

        answer = response.choices[0].message.content
        sources = self._get_sources(context_docs)
        return {"answer": answer, "sources": sources}

    def _get_sources(self, docs: list[str]) -> list[str]:
        found = set()
        combined = " ".join(docs).lower()
        for keyword, source in SOURCE_MAP.items():
            if keyword in combined:
                found.add(source)
            if len(found) >= 3:
                break
        return list(found)
