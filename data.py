import json
import os
from datasets import load_dataset

os.makedirs("./data",exist_ok=True)

print("Downloading dataset from HuggingFace....")

ds=load_dataset("b-mc2/sql-create-context", split="train")

ds=ds.shuffle(seed=40)

train_samples=ds.select(range(1000))

valid_samples=ds.select(range(1000,1150))

def format_row(row):
    """Format into standard structure."""
    system_prompt=(
        "You are an expert SQL generator. Given a database scheme and a natural "
        "Language question, write the exact SQL query that answers the question."

    )

    user_prompt=f"Schema:\n{row['context']}\n\nQuestion:\n{row['question']}"
    assistant_response=row['answer']

    return {
        "messages":[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt},
            {"role":"assistant","content":assistant_response},

        ]
    }

print("Writing ./data/train.jsonl...")


with open("./data/train.jsonl","w",encoding="utf-8") as f:
    for row in train_samples:
        f.write(json.dumps(format_row(row)) + "\n")

with open("./data/valid.jsonl","w",encoding="utf-8") as f:
    for row in valid_samples:
        f.write(json.dumps(format_row(row)) + "\n")

print("Done! data ready in ./data/")
