"""
TEST: MLX Sanity Check
PURPOSE: Verifies that the Apple MLX framework can successfully load the Llama 3 model into Mac Unified Memory and generate 1 token.
Run this if your model is crashing to see if it's a hardware/MLX issue.
"""
import streamlit as st
from mlx_lm import load, generate

@st.cache_resource
def load_model():
    return load("mlx-community/Meta-Llama-3.1-8B-Instruct-4bit")

model, tokenizer = load_model()
print("Model loaded")
generate(model, tokenizer, prompt="Hi", max_tokens=10)
print("Generate 1 success")
