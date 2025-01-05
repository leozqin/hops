from ollama import Client, chat

if __name__ == "__main__":

    client = Client("localhost:8000")
    model = "smollm:1.7b"

    chat = client.chat(
        model=model, messages=[{"role": "user", "content": "Why is the sky blue?"}]
    )

    print(chat.message.content)