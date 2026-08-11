from ollama import chat

response = chat(
    model="qwen3:4b",
    messages=[
        {
            "role": "user",
            "content": " what is the date of India independence."
        }
    ]
)

print(response.message.content)