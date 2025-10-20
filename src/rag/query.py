from ollama import chat

def local_llm_query(prompt: str, model: str = "llama3"):
    """Minimal test for Ollama integration."""
    response = chat(model=model, messages=[{"role": "user", "content": prompt}])
    return response.message.content

if __name__ == "__main__":
    print(local_llm_query("Summarize the purpose of generative AI in one sentence."))