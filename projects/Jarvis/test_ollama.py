import ollama

try:
    response = ollama.chat(
        model="phi3",
        messages=[{"role": "user", "content": "Привет"}],
        timeout=30
    )
    print("✅ Ollama работает:", response['message']['content'])
except Exception as e:
    print("❌ Ошибка:", e)