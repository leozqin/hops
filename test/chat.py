from ollama import Client, chat

if __name__ == "__main__":

    client = Client("localhost:8000")
    model = "smollm2:135m-instruct-q4_0"

    chat = client.chat(
        model=model, messages=[{"role": "user", "content": "Why is the sky blue?"}]
    )

    print(chat.message.content)