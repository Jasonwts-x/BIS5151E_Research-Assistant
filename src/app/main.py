from pathlib import Path
import yaml

def load_config():
    config_path = Path(__file__).resolve().parents[2] / "configs" / "app.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    cfg = load_config()
    print("✅ ResearchAssistantGPT bootstrap")
    print("LLM model:", cfg["llm"]["model"])

if __name__ == "__main__":
    main()
