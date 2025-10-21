from utils.config import load_config

def main():
    cfg = load_config()
    print("✅ ResearchAssistantGPT bootstrap")
    print("LLM provider:", cfg.llm.provider)
    print("LLM model:", cfg.llm.model)
    print("LLM host:", cfg.llm.host)
    print("RAG:", vars(cfg.rag))

if __name__ == "__main__":
    main()