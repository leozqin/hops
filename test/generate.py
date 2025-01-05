from ollama import Client, chat

if __name__ == "__main__":

    client = Client("localhost:8000")
    model = "smollm:1.7b"

    chat = client.generate(model=model, prompt="Why is the sky blue?")

    print(chat.response)