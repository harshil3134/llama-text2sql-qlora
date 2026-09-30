import streamlit as st
from mlx_lm import load, generate

@st.cache_resource
def load_model():
    return load("mlx-community/Meta-Llama-3.1-8B-Instruct-4bit")

model, tokenizer = load_model()
print("Model loaded")
generate(model, tokenizer, prompt="Hi", max_tokens=10)
print("Generate 1 success")
