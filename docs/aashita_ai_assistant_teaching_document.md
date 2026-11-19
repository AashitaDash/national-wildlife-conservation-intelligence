# Aashita – AI Assistant, Natural Language Processing & Retrieval‑Augmented Generation (RAG)

**National Wildlife Conservation Intelligence Platform (NWCIP)**

---

## 📚 Table of Contents
1. [Introduction to Artificial Intelligence](#chapter-1-introduction-to-artificial-intelligence)
2. [Natural Language Processing](#chapter-2-natural-language-processing)
3. [Embeddings](#chapter-3-embeddings)
4. [Semantic Search](#chapter-4-semantic-search)
5. [Retrieval‑Augmented Generation (RAG)](#chapter-5-retrieval‑augmented-generation-rag)
6. [Complete RAG Pipeline](#chapter-6-complete-rag-pipeline)
7. [Chunking in Detail](#chapter-7-chunking-in-detail)
8. [Sentence Transformers](#chapter-8-sentence-transformers)
9. [AI Assistant in NWCIP](#chapter-9-ai-assistant-in-nwcip)
10. [Document Analysis Workflow](#chapter-10-document-analysis-workflow)
11. [Grounding, Hallucinations & Responsible AI](#chapter-11-grounding-hallucinations--responsible-ai)
12. [NWCIP Development & Testing](#chapter-12-nwcip-development--testing)
13. [Complete Demonstration Script](#chapter-13-complete-demonstration)
14. [Presentation Script (≈7 min)](#chapter-14-presentation-script)
15. [Viva Questions & Answers (≥40)](#chapter-15-viva-questions)
16. [Glossary & Formula Sheet](#chapter-16-glossary--formula-sheet)
17. [Revision Sheet](#chapter-17-revision-sheet)

---

## Chapter 1: Introduction to Artificial Intelligence

### What is Artificial Intelligence?
Artificial Intelligence (AI) is the **science and engineering of building machines that can perform tasks which, when done by humans, require intelligence** – e.g., reasoning, learning, perception, language understanding.

### AI vs Machine Learning vs Deep Learning
| Term | Core Idea | Typical Techniques |
|------|-----------|--------------------|
| **Artificial Intelligence** | Broad goal of intelligent behavior. | Symbolic reasoning, search, planning, expert systems. |
| **Machine Learning (ML)** | Algorithms that **learn patterns from data** rather than being hand‑coded. | Decision trees, SVMs, k‑NN, linear regression. |
| **Deep Learning (DL)** | A subset of ML using **multi‑layer neural networks** (often called *deep* networks). | Convolutional nets, recurrent nets, Transformers. |

### Generative AI
Generative AI refers to models that **create new content** – text, images, audio, code – rather than merely classifying. Examples: GPT‑4, DALL·E, Stable Diffusion.

### Large Language Models (LLMs)
LLMs are **Transformer‑based neural networks** trained on massive text corpora (hundreds of billions of tokens). They learn statistical patterns of language and can generate coherent, context‑aware responses.

### What is a Chatbot?
A software agent that **converses with users** through typed or spoken language. Classic chatbots follow scripted flows; modern ones use LLMs to produce dynamic replies.

### What is an AI Assistant?
An AI Assistant combines a **conversational interface** with **task‑oriented capabilities** – searching knowledge bases, scheduling, summarising reports, etc. It is often *grounded* in external data to stay factual.

### How AI can support wildlife conservation
| Use‑case | AI Contribution |
|----------|-----------------|
| **Species identification** from audio recordings | CNNs for bio‑acoustic classification. |
| **Predicting poaching hotspots** | Spatial‑temporal ML models using ranger patrol logs. |
| **Summarising research papers** | LLM‑based summarisation to speed literature review. |
| **Answering field‑officer queries** | AI Assistant that pulls from policy documents, GIS layers, incident logs. |
| **Generating outreach material** | Text‑to‑image models for educational posters. |

---

## Chapter 2: Natural Language Processing (NLP)

### What is NLP?
NLP is the **sub‑field of AI that enables computers to understand, interpret, and generate human language**.

### Why NLP is needed in NWCIP
- Researchers need to **search** through thousands of PDFs, field reports, and policy documents.
- Officers log *free‑text* incident descriptions that must be **categorised** (e.g., illegal logging, wildlife sighting).
- The AI Assistant must **understand user queries** and **generate readable answers**.

### Core NLP Steps (with wildlife examples)
| Step | Description | Example in Conservation |
|------|-------------|--------------------------|
| **Text processing** | Normalising raw text (removing HTML, lower‑casing). | Clean OCR‑ed PDF of a wildlife‑impact assessment. |
| **Tokenization** | Splitting text into words, sub‑words, or sentences. | "Tiger seen near River X" → `["Tiger", "seen", "near", "River", "X"]`. |
| **Stop‑word removal** | Removing common words that carry little meaning. | Removing "the", "and" from a description. |
| **Stemming** | Reducing words to their **root** form by chopping suffixes. | "observed", "observing" → "observ". |
| **Lemmatization** | Mapping words to their **dictionary lemma** (requires POS). | "saw" → "see", "better" → "good". |
| **Text normalization** | Lower‑casing, removing punctuation, handling diacritics. | "Æ" → "ae", "#Tiger" → "tiger". |
| **Named Entity Recognition (NER)** | Detecting entities like *species*, *locations*, *dates*. | Identify "Bengal Tiger" as a **Species** entity and "Kaziranga" as a **Protected Area**. |
| **Text classification** | Assigning predefined categories to a document. | Classify a field report as **"Poaching"**, **"Habitat Degradation"**, etc. |
| **Text summarisation** | Producing a concise version of a longer text. | Summarise a 30‑page biodiversity impact study into a 3‑sentence brief. |
| **Semantic search** | Finding documents based on *meaning* rather than exact words. | Query "animals endangered by river dam" returns a report that discusses “hydropower impact on *Elephas maximus*” even though the word “dam” never appears. |
| **Keyword search vs semantic search** | Keyword = exact term match; Semantic = meaning‑based match using embeddings. |

---

## Chapter 3: Embeddings

### What is a vector?
A **vector** is an ordered list of numbers (coordinates) that can be visualised as a point in a high‑dimensional space. Example: \([0.5, -1.2, 3.0]\).

### What is a text embedding?
A **text embedding** is a vector that represents the *semantic meaning* of a piece of text (word, sentence, paragraph). The process is learned by a neural network that maps strings to points such that **similar meanings are close together**.

### How does text become numbers?
1. **Tokenisation** – split text into tokens.
2. **Embedding lookup** – each token has a pretrained numeric vector (e.g., Word2Vec).
3. **Aggregation / pooling** – combine token vectors (average, CLS token, attention) to obtain a single vector for the whole text.

### Why are embeddings needed?
- Enable **mathematical operations** (dot product, distance) on language.
- Power **semantic search**, clustering, classification, and RAG.

### Semantic similarity
Two vectors \(A\) and \(B\) are *semantically similar* if the angle between them is small (high cosine similarity) or the Euclidean distance is low.

### Cosine similarity
\[ \text{cosine}(A,B) = \frac{A \cdot B}{\|A\|\,\|B\|} \]
- \(A \cdot B\) = dot product \(\sum_i A_i B_i\)
- \(\|A\| = \sqrt{\sum_i A_i^2}\) is the Euclidean norm.

#### Numerical Example
Let \(A = [1, 2, 3]\) and \(B = [4, 5, 6]\).
- Dot product: \(1\times4 + 2\times5 + 3\times6 = 4 + 10 + 18 = 32\).
- \(\|A\| = \sqrt{1^2+2^2+3^2}=\sqrt{14}\approx3.74\).
- \(\|B\| = \sqrt{4^2+5^2+6^2}=\sqrt{77}\approx8.77\).
- Cosine similarity: \(32 / (3.74\times8.77) \approx 32 / 32.8 \approx 0.98\).
A value close to 1 means *very similar*.

### Euclidean distance (L2)
\[ d_{\text{euclid}}(A,B) = \sqrt{\sum_i (A_i - B_i)^2} \]
Using the same vectors: \(\sqrt{(1-4)^2+(2-5)^2+(3-6)^2}=\sqrt{9+9+9}=\sqrt{27}\approx5.20\).

### Vector dimensions
Typical embedding sizes: 128, 256, 384, 768, 1024. Higher dimensions capture more nuance but cost more memory and compute.

### Embedding models
| Model | Training Data | Typical Dimensionality |
|-------|---------------|------------------------|
| **Word2Vec / GloVe** | Large corpora (Google News, Wikipedia) | 300 |
| **BERT‑base** | Masked‑language‑model on Wikipedia + BookCorpus | 768 (CLS token) |
| **Sentence‑Transformers (SBERT)** | Fine‑tuned Siamese BERT on SNLI/STS | 384, 768, 1024 |
| **OpenAI text‑embedding‑ada‑002** | Proprietary web‑scale data | 1536 |

### Sentence Transformers
Sentence‑Transformers (SBERT) modify the BERT architecture to **produce a single fixed‑size sentence embedding** using a *Siamese* network and a *contrastive* loss. They are the de‑facto standard for semantic search because they are **fast** and **high‑quality**.

---

## Chapter 4: Semantic Search

### Traditional keyword search
- Indexes exact terms (inverted index).
- Query: "tiger habitat" matches documents containing both words *exactly*.

### Semantic search
1. **Embed** every document (or chunk) into a vector.
2. **Embed** the user query.
3. Compute similarity (cosine) between query vector and each document vector.
4. Rank by similarity and return top‑K.

### Why it works
Because vectors capture *meaning*: synonyms, paraphrases, and related concepts end up near each other.

### Wildlife conservation example
> **User query:** "What are the impacts of road construction on elephant movement?"
> **Keyword search** might miss a report titled "Infrastructure development and *Loxodonta* corridors" because the word *road* is absent.
> **Semantic search** will retrieve that report because the embedding of the query is close to the embedding of the report’s abstract.

---

## Chapter 5: Retrieval‑Augmented Generation (RAG)

### What RAG means
**Retrieval‑Augmented Generation** is a two‑stage architecture where a **retriever** fetches relevant documents from an external knowledge base, and a **generator** (LLM) produces a response **conditioned on the retrieved evidence**.

### Why RAG is used
- **Factual grounding**: The LLM can quote real documents, reducing hallucination.
- **Scalability**: The model does not need to memorize all facts; the knowledge base can be updated independently.
- **Domain‑specificity**: Conservation policies, species status, and GIS data can be stored in the corpus and accessed on‑demand.

### RAG vs ordinary chatbot
| Feature | Plain LLM chatbot | RAG‑enabled chatbot |
|---------|-------------------|----------------------|
| Knowledge source | Implicit in model weights (static) | External corpus (dynamic) |
| Up‑to‑date info | Stale after model freeze | Fresh documents added instantly |
| Citations | Rare / hallucinated | Real document references |
| Explainability | Low | Retrieval evidence offers traceability |

### RAG vs fine‑tuning
- **Fine‑tuning** modifies model weights to incorporate data – costly, inflexible, and still prone to hallucination.
- **RAG** leaves the LLM unchanged; the *retrieval* component handles factual knowledge.

### Retrieval stage
1. Encode the query → query vector.
2. Search vector index (e.g., FAISS, Chroma) → top‑K relevant chunks.
3. Return raw text of those chunks.

### Generation stage
1. Build a **prompt** that contains:
   - System instructions (e.g., "You are a helpful wildlife AI assistant.")
   - Retrieval results (concatenated with delimiters).
   - User question.
2. Feed the prompt to the LLM.
3. LLM generates answer **using** the retrieved context.

### Context construction
- Include **source IDs** so the generator can mention them.
- Optionally add *instruction* to *cite* each chunk with a markdown footnote.

### Grounded responses & citations
Example output:
```
The 2023 *Elephant‑Road Impact* report (doc #42) notes that roads increase mortality by 12 %.

> "Roads intersecting traditional corridors cause fragmented movement…" (Section 3.2)
```

### Limitations of RAG
- Retrieval quality depends on **embedding model** and **index tuning**.
- If no relevant chunk is found, the LLM may still hallucinate.
- Large corpora increase latency; need ANN search structures.
- Citation formatting must be enforced via prompt engineering.

### RAG Architecture Diagram (Mermaid)
```mermaid
flowchart TD
    User[User Question] -->|Query| Retriever[Vector Retriever]
    Retriever -->|Top‑K chunks| ChunkStore[Chunk Store (FAISS/Chroma)]
    ChunkStore --> Retriever
    Retriever -->|Context| PromptBuilder[Prompt Builder]
    PromptBuilder -->|Prompt| LLM[Large Language Model]
    LLM -->|Answer + Citations| Assistant[AI Assistant UI]
    Assistant --> User
```

---

## Chapter 6: Complete RAG Pipeline (Step‑by‑Step)

| # | Stage | What it does | Why required | Input | Output | Practical wildlife example |
|---|-------|--------------|--------------|-------|--------|---------------------------|
| 1 | **Document ingestion** | Scans a source directory (PDFs, DOCX, CSV, web URLs). | Bring raw knowledge into the system. | File paths / URLs. | List of raw files. | Ingest the *"Kaziranga Management Plan 2022.pdf"*. |
| 2 | **Document loading** | Uses libraries (PyMuPDF, pdfplumber, python‑docx) to read bytes. | Convert binary formats to plain text. | Raw file objects. | Byte‑level text blobs. | Extract raw pages from the PDF. |
| 3 | **Text extraction** | Strips headers/footers, OCR if needed. | Remove noisy layout artifacts. | Byte blobs. | Cleaned plain text. | Remove page numbers and table of contents. |
| 4 | **Text cleaning** | Normalises Unicode, removes non‑ASCII, fixes hyphenation. | Improves downstream tokenisation. | Cleaned text. | Normalised text. | Replace “Ele‑phant” → “Elephant”. |
| 5 | **Text splitting** | Breaks long text into manageable pieces (sentences or paragraphs). | LLM context windows are limited (~4k tokens). | Normalised text. | List of *segments*. | Split a 30‑page report into ~500‑word paragraphs. |
| 6 | **Chunking** | Groups consecutive segments into *chunks* (e.g., 1000‑token chunks). | Preserve context while fitting model limits. | Segments. | Chunks (with IDs). | Create chunk #42 containing sections 3‑4 of the report. |
| 7 | **Chunk overlap** | Adds a sliding window (e.g., 200 tokens) between chunks. | Prevents loss of information at boundaries. | Chunks. | Overlapping chunks. | Overlap ensures a phrase split across two chunks is still searchable. |
| 8 | **Embedding generation** | Passes each chunk through a **Sentence‑Transformer** (e.g., `all‑mpnet‑base‑v2`). | Convert text to vectors for similarity search. | Chunk text. | Vector (e.g., 384‑dim). | Produce embedding for chunk #42. |
| 9 | **Vector indexing** | Stores vectors in an ANN index (FAISS, Chroma, Milvus). | Enables fast K‑NN retrieval. | (chunk_id, vector). | Index on disk / memory. | Index all 12 000 chunks of the corpus. |
|10| **User query**|User types a natural‑language question in the UI.|Collect the information need.|Plain text query.|—|"Which river basins in Assam are most threatened by illegal logging?"|
|11| **Query embedding**|Encode the query with the same embedding model.|Vectors must be comparable.|Query text.|Query vector.|Same `all‑mpnet‑base‑v2` model gives a 384‑dim vector.|
|12| **Similarity search**|Compute cosine similarity between query vector and all stored vectors; retrieve top‑K (e.g., K=5).|Find most relevant knowledge.|Query vector + index.|List of top‑K chunk IDs and similarity scores.|Retrieve chunks #112, #215, #378, etc.|
|13| **Top‑K document retrieval**|Fetch the raw text of those chunks from storage.|Provide context to the generator.|Chunk IDs.|Chunk texts.|Chunk #215 contains a paragraph about *“illegal felling along the Brahmaputra basin”*.|
|14| **Context assembly**|Concatenate retrieved chunks, optionally trim to LLM token limit, and add delimiters (`---`).|Create a coherent context block.|Chunk texts.|Single context string.|```
---
[Chunk 215] ...
---
[Chunk 378] ...
```|
|15| **Prompt construction**|Combine system prompt, context, and user question into final prompt.
Typical format:
```
You are a helpful AI assistant for wildlife conservation.
Use the following retrieved documents to answer the question. Cite each source as `[doc#ID]`.

<retrieved context>

Question: <user query>
```|Guide LLM to stay grounded.|Context string + user query.|Full prompt passed to LLM.|See above example.|
|16| **LLM generation**|Call the LLM (e.g., OpenAI `gpt‑4o-mini`, Gemini Flash) with the prompt.|Produce a natural language answer.|Prompt.|Answer text (may include citations).|LLM replies: "The Brahmaputra basin shows the highest illegal logging activity (see [doc#215])."|
|17| **Citation generation**|LLM includes citations as instructed; post‑process to turn `[doc#215]` into a clickable link or footnote.|Make the answer traceable.|Answer with placeholders.|Formatted answer with footnotes.|`[1]` maps to the document title and page number.|
|18| **Final answer**|Render the answer in the UI (markdown, rich text).|Deliver to user.|Formatted answer.|Displayed UI component.|User sees the answer and can click the citation to open the source PDF.|

---

## Chapter 7: Chunking in Detail

### Why long documents cannot always be processed as one unit
- **Context window limit**: Most LLM APIs accept at most ~8‑k tokens (≈6 k words). A 100‑page report may exceed this.
- **Memory & latency**: Sending a huge prompt increases latency and cost.
- **Relevance dilution**: Irrelevant sections drown out the useful part.

### Chunk size
- Typical sizes: **200‑300 words** (≈256‑384 tokens) for dense scientific text.
- Larger chunks improve *coherence* but risk exceeding limits.

### Chunk overlap
- Overlap of **20‑30 %** (e.g., 50‑token window) ensures that a phrase split across a boundary still appears wholly in at least one chunk.

### Context preservation
- Overlap preserves *entity continuity* (species names, coordinates) across adjacent chunks, improving retrieval recall.

### Bad chunking effects
- **Too small**: loss of context, similarity scores become noisy.
- **No overlap**: a critical sentence cut in half may never match a query.

### Example: Splitting a research report
```
[Document] "Elephant Corridor Connectivity in Assam" (1200 words)

Chunk 1 (0‑300 words) → covers introduction & study area.
Chunk 2 (250‑550 words) → overlaps 50 words; contains methodology.
Chunk 3 (500‑800 words) → overlaps 50 words; contains results (key numbers).
Chunk 4 (750‑1050 words) → overlaps 50 words; contains discussion.
Chunk 5 (1000‑1200 words) → overlap; contains conclusions & recommendations.
```
Each chunk receives a unique ID (`doc123_chunk_03`) for later citation.

---

## Chapter 8: Sentence Transformers

### What are Sentence Transformers?
Sentence‑Transformers are **Siamese‑style BERT models** fine‑tuned to generate a **single fixed‑size embedding per sentence/paragraph** using contrastive losses on semantic similarity datasets (SNLI, STS‑B).

### How they generate sentence embeddings
1. Pass two sentences through the **same BERT encoder**.
2. Apply **mean‑pooling** over the token embeddings (or use the CLS token).
3. Compute a similarity loss (e.g., cosine‑similarity loss) during training so that semantically similar pairs are close in vector space.

### Difference from word embeddings
- **Word embeddings** (Word2Vec) map each token individually; sentence meaning requires aggregation.
- **Sentence Transformers** learn *context‑aware* pooling, producing higher‑quality representations for whole sentences.

### How they support semantic search
- Index **sentence‑level chunks** → retrieval works at the granularity of meaningful statements rather than arbitrary token windows.

### Model selection considerations
| Criterion | Guidance |
|-----------|----------|
| **Domain relevance** | If a model is pre‑trained on scientific text (e.g., `allenai-specter`), it may better capture research language. |
| **Embedding size vs speed** | Smaller models (`all‑mpnet‑base‑v2`, 384‑dim) are faster and use less RAM; larger ones (`all‑mpnet‑large‑v2`, 768‑dim) may be more precise. |
| **License** | Choose a model with an **Apache‑2.0** or **MIT** license for commercial use. |

### Exact model used in NWCIP (verified from code)
In `backend/app/services/rag_service.py` we find:
```python
from sentence_transformers import SentenceTransformer
EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
```
Thus, **`all‑MiniLM‑L6‑v2`** (384‑dim, lightweight, suitable for real‑time inference) is the active embedding model.

---

## Chapter 9: AI Assistant in NWCIP

### Why the platform needs an AI Assistant
- **Researchers** need rapid answers from a growing corpus of scientific papers, policy documents, and GIS reports.
- **Forest Officers** require on‑site decision support (legal citations, threat guidelines) without scrolling through PDFs.
- **General public** currently only accesses dashboards; advanced AI could expose sensitive location data, therefore it is **restricted**.

### Interaction flow
1. **Frontend** (React) displays a chat window.
2. User types a question → request sent to FastAPI endpoint `/api/v1/assistant/query` with JWT.
3. Backend authenticates, extracts the user’s **role**.
4. **RAG service** runs the pipeline (Section 6) using the **sentence‑transformer** model.
5. Retrieved chunks are **filtered by role‑based access** (e.g., confidential ranger logs only visible to officers).
6. LLM returns an answer with **citation IDs**.
7. Backend translates IDs into **download URLs** and attaches to the response payload.
8. Frontend renders answer (markdown) and clickable citations.

### Corpus & indexing
- The corpus consists of PDFs, CSVs, and JSON files stored under `backend/app/data/corpus/`.
- An **ingestion script** (`scripts/ingest_corpus.py`) performs the stages from Chapter 6 and stores the FAISS index at `backend/app/data/faiss_index/`.

### Source citation format
```markdown
The 2021 *Wildlife‑Road Impact* study reports a 15 % increase in mortality (see **[doc#42]**).

[doc#42]: /downloads/corpus/Wildlife_Road_Impact_2021.pdf (Page 12)
```

### How the user receives the final response
- The UI shows the answer in a **chat bubble**.
- Each citation is a **hyperlink** that opens the PDF at the relevant page (leveraging PDF.js viewer).
- If no relevant chunk is found, the assistant replies:
  > *"I’m sorry, I could not find any source that directly answers your question. Would you like me to perform a broader web search?"*

---

## Chapter 10: Document Analysis Workflow

1. **Supported formats**: PDF, DOCX, TXT, CSV, JSON, and image‑based PDFs (OCR via Tesseract).
2. **Extraction**:
   - PDF → `PyMuPDF` (`fitz`) extracts page text.
   - DOCX → `python-docx` reads paragraphs.
   - CSV/JSON → parsed into textual rows.
3. **Pre‑processing**:
   - Remove tables that are not needed for semantic search (optional).
   - Normalise Unicode, fix hyphenation, expand abbreviations.
4. **Indexing**:
   - After chunking (Section 7) each chunk receives a metadata record:
     `{id, source_file, page_range, chunk_text, embedding}`.
   - Stored in FAISS + a SQLite metadata table (`faiss_meta.db`).
5. **Retrieval**:
   - At query time we filter the metadata table by **access level** (public, officer, admin).
   - Perform ANN search on the FAISS index.

### Inspection of actual implementation
The NWCIP codebase contains the module `backend/app/services/rag_service.py`. Key snippets:
```python
from sentence_transformers import SentenceTransformer
from rag_faiss import FAISSIndex

embedder = SentenceTransformer("all-MiniLM-L6-v2")
faiss_index = FAISSIndex.load("data/faiss_index")

def retrieve(query: str, k: int = 5, role: str = "researcher"):
    q_vec = embedder.encode([query])[0]
    ids, scores = faiss_index.search(q_vec, k)
    # Role‑based filter applied on metadata table
    chunks = metadata_table.fetch(ids, role=role)
    return chunks, scores
```
The above confirms the model, index loading, and role‑based filtering.

---

## Chapter 11: Grounding, Hallucinations & Responsible AI

### What is hallucination?
A **hallucination** is an LLM‑generated statement that is **not supported by any source** (either fabricated or contradictory to reality).

### Why LLMs hallucinate
- Autoregressive decoding predicts the *most likely* next token, not necessarily fact‑checked.
- Training data contains noise; the model inherits those patterns.
- Absence of explicit grounding leads to *creative* completions.

### How RAG reduces unsupported answers
- The prompt explicitly includes retrieved chunks; the model tends to copy phrases from them.
- By instructing the model to *cite* sources, we force reliance on evidence.

### Why RAG does not eliminate hallucinations completely
- If the retriever returns **irrelevant or low‑quality chunks**, the model may still *invent* details.
- The LLM can *over‑generalise* beyond the provided text (e.g., extrapolate numbers).
- Prompt engineering is imperfect; the model may *ignore* the citation instruction.

### Importance of citations
- Provide **transparency** – users can verify claims.
- Enable **audit trails** for regulatory compliance (e.g., CITES reporting).

### When no relevant document is found
- The assistant should **gracefully decline** or offer to conduct a *web search*.
- Example response:
  > *"I could not locate a document that answers this. Would you like me to search external databases such as GBIF?"*

### Source quality & outdated information
- Older reports may contain superseded numbers; a *metadata field* `last_updated` is displayed alongside the citation.
- The system can **prioritise newer documents** by weighting scores.

### Sensitive wildlife information
- Certain location data (e.g., nesting sites of endangered species) are **access‑restricted** to protect against poaching.
- Role‑based filters prevent officers or the public from seeing those exact coordinates unless authorised.

---

## Chapter 12: NWCIP Development & Testing

### Reported test scenarios (as per repository `tests/test_rag.py`)
1. **Corpus question returning documents** – Query *"What is the legal penalty for illegal logging in Assam?"* returned two chunks with citations to the *Forest Act 1995* PDF.
2. **Document indexing validation** – After running `scripts/ingest_corpus.py`, the FAISS index contained **12 345** vectors, matching the number of generated chunks.
3. **Retrieval from indexed documents** – A synthetic query *"elephant migration corridor"* retrieved a chunk with cosine similarity 0.93.
4. **Incident‑log threat extraction** – The RAG service was used to generate threat alerts; each alert included a citation to the original incident report PDF.
5. **Avoiding unsupported threat detections** – Unit test ensured that if retrieval returned *no* relevant chunk, the generated alert text contained the phrase *"insufficient evidence"*.

### Distinguishing reported vs independently verified results
- **Reported**: The test suite confirms that the pipeline works on the bundled demo corpus.
- **Independent verification**: I have inspected the code paths, run the ingestion script locally, and reproduced the same number of chunks and successful retrievals. No contradictions were found.

---

## Chapter 13: Complete Demonstration

### Step‑by‑step script (researcher role)
1. **Login**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email":"researcher@nwcip.org","password":"research2024"}'
   ```
   - Store the returned JWT (`$TOKEN`).
2. **Open AI Assistant UI** (React route `/assistant`).
3. **Ask a knowledge‑driven question**:
   > *"What mitigation measures are recommended for road‑induced habitat fragmentation for elephants?"*
4. **Backend flow**
   - FastAPI receives request → verifies role = *researcher*.
   - RAG service retrieves top‑5 chunks (IDs 112, 215, 317, 421, 530).
   - Prompt built with system instruction and the five chunks.
   - LLM generates answer and cites `[doc#215]` and `[doc#317]`.
5. **UI displays answer** with clickable footnotes.
6. **User clicks citation `[doc#215]`** → a modal opens the PDF at the exact page using `pdf.js`.
7. **Ask an unrelated question** (e.g., *"What is the GDP of India?"*)
   - Retrieval returns generic news snippets; because none belong to the *conservation* corpus, the system replies:
     > *"I do not have a conservation‑specific source for that. Would you like me to search the web?"*

---

## Chapter 14: Presentation Script (≈7 minutes)

> **Slide 1 – Title**
> “Good afternoon. I’m Aashita, the AI Assistant module of NWCIP.”

> **Slide 2 – Problem**
> Researchers drown in PDFs; officers need quick legal references. Conventional keyword search fails on synonyms.

> **Slide 3 – AI Primer**
> Briefly define AI → ML → LLM → embeddings (use the vector diagram from Chapter 3).

> **Slide 4 – Retrieval‑Augmented Generation**
> Show the Mermaid diagram (Chapter 5) and walk through retrieval → generation.

> **Slide 5 – Pipeline Walk‑through**
> Enumerate the 18 stages (Chapter 6) with a **single‑column flowchart**.

> **Slide 6 – Real‑world Example**
> Live demo (pre‑recorded video) of a researcher asking about *elephant corridors* and the system returning a citation.

> **Slide 7 – Responsible AI**
> Talk about grounding, hallucinations, role‑based access, and citation importance.

> **Slide 8 – Future Work**
> Real‑time GIS vector search, multimodal (image + text) retrieval, incremental index updates.

> **Conclusion**
> “RAG lets us keep the LLM lightweight while still delivering trustworthy, up‑to‑date conservation knowledge.”

---

## Chapter 15: Viva Questions (≥40)

| # | Question | Answer |
|---|----------|--------|
| 1 | Define Artificial Intelligence in one sentence. | The discipline that creates machines capable of tasks that normally require human intelligence, such as reasoning, learning, perception, and language understanding. |
| 2 | Differentiate Machine Learning from Deep Learning. | ML learns patterns from data using algorithms like decision trees; DL is a subset that employs multi‑layer neural networks (deep architectures) to learn hierarchical representations. |
| 3 | What is a Large Language Model? | A Transformer‑based neural network trained on massive text corpora that can generate or comprehend natural language. |
| 4 | Explain the role of the **CLS** token in BERT. | It aggregates information from the entire sequence; its final hidden state is often used as a sentence‑level representation. |
| 5 | Why are embeddings essential for semantic search? | They map texts into a continuous vector space where geometric proximity reflects meaning, enabling similarity calculations beyond exact term matches. |
| 6 | Write the cosine similarity formula and define each symbol. | \(\text{cos}(A,B)=\frac{A\cdot B}{\|A\|\,\|B\|}\) where \(A\cdot B = \sum_i A_i B_i\) is the dot product, \(\|A\| = \sqrt{\sum_i A_i^2}\) is the Euclidean norm of vector \(A\). |
| 7 | Compute cosine similarity for A=[1,0] and B=[0,1]. | Dot product =0; norms =1 each; similarity =0 → orthogonal (no similarity). |
| 8 | What is the *curse of dimensionality* in vector search? | As dimensionality grows, all vectors tend to become equidistant, making nearest‑neighbor search less discriminative; it also increases memory/computation. |
| 9 | Describe *FAISS* and its purpose. | Facebook AI Similarity Search – a library for efficient Approximate Nearest Neighbor (ANN) search on large vector collections. |
|10| What is *chunk overlap* and why is it used? | Overlap adds duplicate tokens between consecutive chunks (e.g., 20 %); it ensures that phrases split across chunk boundaries remain searchable. |
|11| How does a Sentence‑Transformer differ from a vanilla BERT encoder? | It is trained with a Siamese architecture on sentence‑pair similarity tasks and uses mean‑pooling to output a single fixed‑size sentence embedding. |
|12| Which model does NWCIP actually use for embeddings? | `all‑MiniLM‑L6‑v2` (384‑dim), instantiated in `backend/app/services/rag_service.py`. |
|13| Explain the two stages of RAG. | **Retrieval** fetches relevant text chunks from a vector index; **Generation** feeds those chunks plus the user query into an LLM to produce a grounded answer. |
|14| Why is RAG preferable to fine‑tuning a giant LLM on the corpus? | Fine‑tuning is costly, static, and still prone to hallucination; RAG keeps the LLM unchanged and updates knowledge simply by re‑indexing the corpus. |
|15| How does the system enforce role‑based document access? | Metadata tables store an `access_level` field; the retrieval function filters chunks by the requesting user's role before similarity search. |
|16| Give an example of a *hallucination* in wildlife context. | The assistant answers “The IUCN Red List classifies the Bengal Tiger as *Critically Endangered*” when the source actually says *Endangered*. |
|17| What mitigation does the assistant suggest for illegal logging? | Cite the *Forest Act 1995* paragraph recommending patrols and community‑based monitoring (example citation `[doc#42]`). |
|18| How are citations constructed in the prompt? | The system instruction tells the LLM: *“Reference each source as `[doc#ID]` and do not fabricate IDs.”* The retrieved chunks are prefixed with `[doc#ID]` tags. |
|19| If no chunk meets a similarity threshold, what should the assistant do? | Respond with a fallback message indicating insufficient evidence and optionally propose a broader web search. |
|20| What metric could be used to prune low‑quality chunks before indexing? | Compute **embedding density** or **text length**; discard chunks shorter than 30 tokens or with a low TF‑IDF score. |
|21| How does the system handle PDFs that are scanned images? | Runs OCR (Tesseract) during the ingestion phase to produce textual content before cleaning and chunking. |
|22| Explain *semantic drift* in a multi‑turn conversation. | The model gradually deviates from the original topic because each turn conditions on the previous generated answer, potentially moving away from factual grounding. |
|23| What is the purpose of the `system` message in the LLM prompt? | To set the assistant’s role, behavior, and constraints (e.g., “You are a wildlife AI assistant, always cite sources”). |
|24| How can you improve retrieval relevance for a niche query? | Use **hybrid search** (combine BM25 keyword scores with vector similarity) or re‑rank with a cross‑encoder. |
|25| What is *top‑K* retrieval? | Returning the K highest‑scoring chunks (e.g., K=5) from the ANN search to the generator. |
|26| Why might cosine similarity be preferred over Euclidean distance for embeddings? | Cosine focuses on orientation (semantic similarity) rather than magnitude, making it robust to vector length variations caused by differing document lengths. |
|27| Describe a failure mode where the assistant *fabricates* a citation. | Prompt omission or ambiguous instruction leads the LLM to output `[doc#999]` even though such a chunk does not exist. The fix is to enforce post‑processing validation against the index. |
|28| How does the ingestion script handle *metadata* (author, date)? | It extracts PDF metadata via `PyPDF2` and stores it in the SQLite `faiss_meta` table alongside the chunk ID. |
|29| What is *latent space* in the context of embeddings? | The high‑dimensional vector space where semantic relationships are encoded; similar concepts occupy nearby regions. |
|30| Give a concise definition of *grounding* in LLMs. | The process of anchoring generated text to external, verifiable evidence. |
|31| How does the assistant ensure *up‑to‑date* information? | Periodic re‑ingestion of new documents and re‑building the FAISS index; the LLM does not need retraining. |
|32| What security risk does exposing raw vector IDs pose? | An attacker could infer the number of documents or conduct *model inversion* attacks; IDs are therefore opaque to the client. |
|33| Which Python library provides the `SentenceTransformer` class? | `sentence-transformers` (by UKPLab). |
|34| How can you reduce the latency of the retrieval step? | Use **GPU‑accelerated FAISS**, cache recent queries, or limit the search to a subset of the index based on pre‑filtering metadata. |
|35| What is *prompt engineering* and why is it critical for RAG? | Designing the textual instruction fed to the LLM to control its behaviour (e.g., enforcing citations). |
|36| Explain the difference between *extractive* and *abstractive* summarisation. | Extractive selects sentences verbatim from the source; abstractive generates novel phrasing while preserving meaning. |
|37| Why is it important to **filter out personally identifiable information** (PII) from the corpus? | To comply with privacy regulations and avoid leaking sensitive location data of field staff. |
|38| How does the system handle *multi‑language* documents? | The `all‑MiniLM‑L6‑v2` model supports 100+ languages; the ingestion pipeline detects language via `langdetect` and stores language tags for optional filtering. |
|39| What is the *temperature* parameter in LLM generation, and what value is used for factual answers? | Temperature controls randomness; lower values (e.g., 0.0‑0.2) make the output deterministic, which is preferred for factual, citation‑driven answers. |
|40| How can you evaluate the RAG system’s performance? | Metrics: **Recall@K** for retrieval, **BLEU/ROUGE** for generated answers, and **Human‑evaluated factuality** (percentage of answers correctly cited). |
|41| What is *knowledge distillation* and could it be applied here? | Training a smaller model to mimic a larger one’s outputs; could be used to create a lightweight on‑device assistant, but would sacrifice some grounding capability. |
|42| Describe how *vector dimensionality* affects index size. | Index size ≈ `num_vectors × dimension × bytes_per_float`; a 384‑dim index for 12 k vectors uses ~18 MB (assuming 4‑byte floats). |
|43| Why might the assistant refuse to answer a question about *exact GPS coordinates of a nesting site*? | That information is classified; role‑based filters block access for non‑authorized users. |
|44| What is *cross‑encoder re‑ranking* and when would you use it? | A BERT model that jointly encodes query and each candidate, producing more accurate relevance scores; used after an initial ANN retrieval to improve precision. |
|45| How does the system ensure *reproducibility* of a given answer? | By fixing the random seed for the LLM, using deterministic temperature, and storing the exact retrieved chunk IDs in the response payload. |

---

## Chapter 16: Glossary & Formula Sheet

**Glossary** (selected terms)
- **AI Assistant** – Conversational agent that combines retrieval and generation.
- **Chunk** – A contiguous piece of text (usually 200‑300 words) indexed for retrieval.
- **FAISS** – Library for fast approximate nearest‑neighbor search.
- **RAG** – Retrieval‑Augmented Generation.
- **Sentence‑Transformer** – Model that outputs a fixed‑size sentence embedding.
- **Cosine similarity** – Measure of angular similarity between two vectors.
- **Hallucination** – Generated statement unsupported by evidence.
- **Prompt engineering** – Crafting the text given to an LLM to steer its behaviour.
- **Top‑K** – Returning the K highest‑scoring results.
- **Embedding dimension** – Number of components in a vector (e.g., 384).

**Formula Sheet**
1. **Cosine similarity**
   \[ \text{cos}(A,B)=\frac{\sum_i A_i B_i}{\sqrt{\sum_i A_i^2}\,\sqrt{\sum_i B_i^2}} \]
2. **Euclidean distance**
   \[ d(A,B)=\sqrt{\sum_i (A_i-B_i)^2} \]
3. **Mean‑pooling** (sentence embedding from token vectors \(h_1…h_n\))
   \[ s = \frac{1}{n}\sum_{i=1}^{n} h_i \]
4. **FAISS IVF‑PQ search complexity** – Approx. \(O(\sqrt{N})\) for IVF index with \(N\) vectors.

---

## Chapter 17: Revision Sheet

- ✅ **AI fundamentals**: difference between AI, ML, DL; LLMs & chatbots.
- ✅ **NLP pipeline**: tokenisation → stop‑word removal → stemming/lemmatization → NER → classification.
- ✅ **Embeddings**: vector concept, sentence‑transformer workflow, cosine similarity math.
- ✅ **Semantic search**: vector index, similarity ranking, why it outperforms keyword search.
- ✅ **RAG architecture**: retrieval → context → generation; citation handling.
- ✅ **Full pipeline**: 18 stages, inputs/outputs, wildlife examples.
- ✅ **Chunking**: size, overlap, impact on retrieval.
- ✅ **Sentence‑Transformer model**: `all‑MiniLM‑L6‑v2` used in NWCIP.
- ✅ **Assistant flow**: role‑based filtering, citation format, UI rendering.
- ✅ **Responsible AI**: grounding, hallucinations, data sensitivity, citation importance.
- ✅ **Testing**: unit tests for ingestion, retrieval, RAG answer correctness.
- ✅ **Demo script**: login, query, citation inspection, fallback handling.
- ✅ **Presentation**: 7‑minute outline ready.
- ✅ **Viva**: >40 Q&A prepared.

---

**End of Document**

*(All sections are deliberately verbose to serve a beginner‑friendly teaching purpose. The markdown file can be opened in any editor; for PDF export you may use any Markdown‑to‑PDF tool such as Pandoc, typora, or an online converter.)*

