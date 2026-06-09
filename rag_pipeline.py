import pandas as pd
from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
INDEX_NAME = "healthcare-rag"

def get_embedding(text):
    """Use Pinecone's built-in inference for embeddings"""
    result = pc.inference.embed(
        model="multilingual-e5-large",
        inputs=[text],
        parameters={"input_type": "passage"}
    )
    return result[0].values

def init_pinecone():
    existing = [i.name for i in pc.list_indexes()]
    if INDEX_NAME not in existing:
        pc.create_index(
            name=INDEX_NAME,
            dimension=1024,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    return pc.Index(INDEX_NAME)

def row_to_text(row):
    return (
        f"Patient age {int(row['age']/365)}, "
        f"gender {'female' if row['gender']==1 else 'male'}, "
        f"BP {row['ap_hi']}/{row['ap_lo']}, "
        f"cholesterol {row['cholesterol']}, "
        f"glucose {row['gluc']}, "
        f"smoker {'yes' if row['smoke']==1 else 'no'}, "
        f"alcohol {'yes' if row['alco']==1 else 'no'}, "
        f"active {'yes' if row['active']==1 else 'no'}, "
        f"cardio risk {row['cardio']}"
    )

def ingest_data(sample_size=500):
    index = init_pinecone()
    df = pd.read_csv("data/cardio_train.csv", sep=";").head(sample_size)
    texts = [row_to_text(row) for _, row in df.iterrows()]

    vectors = []
    for i, text in enumerate(texts):
        embedding = get_embedding(text)
        vectors.append({
            "id": str(i),
            "values": embedding,
            "metadata": {"text": text}
        })
        if i % 50 == 0:
            print(f"Processed {i}/{len(texts)}")

    # Upsert in batches of 100
    for i in range(0, len(vectors), 100):
        index.upsert(vectors=vectors[i:i+100])

    print(f"Ingested {len(vectors)} records into Pinecone ✅")

def retrieve_similar(patient_text, top_k=3):
    index = init_pinecone()
    embedding = get_embedding(patient_text)
    results = index.query(vector=embedding, top_k=top_k, include_metadata=True)
    return [r["metadata"]["text"] for r in results["matches"]]