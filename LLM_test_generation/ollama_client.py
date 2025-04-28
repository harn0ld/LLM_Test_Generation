# ollama_client.py
import requests


class OllamaClient:
    def __init__(self, base_url="http://localhost:11434", model_name="codellama:latest"):
        self.base_url = base_url
        self.model_name = model_name

    def generate(self, prompt, temperature=0.2, max_tokens=None):
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False
        }
        if max_tokens:
            payload["num_predict"] = max_tokens

        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with Ollama: {e}")
            return None

