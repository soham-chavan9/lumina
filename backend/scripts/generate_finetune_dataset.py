import json
import random
import os

INPUT = "data/cleaned_texts/dataset.json"
OUTPUT = "data/finetuning/finetune_data.jsonl"

os.makedirs("data/finetuning", exist_ok=True)
SYSTEM_PROMPT = "You are Lumina, a compliance expert."

def generate_dataset():
    with open(INPUT) as f:
        data = json.load(f)
    docs = {}
    for d in data:
        docs.setdefault(d["doc"], []).append(d["chunk"])

    examples = []
    for doc, chunks in docs.items():
        for chunk in random.sample(chunks, min(3, len(chunks))):
            q = f"What does '{doc}' say about data protection or compliance?"
            a = chunk[:400] + "..."
            examples.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": q},
                    {"role": "assistant", "content": a}
                ]
            })

    with open(OUTPUT, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")

    print(f"✅ Created {len(examples)} fine-tuning samples at {OUTPUT}")

if __name__ == "__main__":
    generate_dataset()
