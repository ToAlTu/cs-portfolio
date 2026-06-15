import os
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def summarize_text(text):
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="You are a helpful assistant that summarizes text clearly and concisely. Only summarize the content — do not comment on costs, tokens, or API pricing.",
        messages=[
            {"role": "user", "content": f"Please summarize the following text in 3 bullet points:\n\n{text}"}
        ]
    )
    
    # Token tracking
    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens
    
    # Sonnet 4.6 pricing
    input_cost = (input_tokens / 1_000_000) * 3.00
    output_cost = (output_tokens / 1_000_000) * 15.00
    total_cost = input_cost + output_cost
    
    print(f"\n--- Usage ---")
    print(f"Input tokens:  {input_tokens}")
    print(f"Output tokens: {output_tokens}")
    print(f"Cost:          ${total_cost:.6f}\n")
    
    return message.content[0].text

if __name__ == "__main__":
    print("=== Text Summarizer ===")
    print("Paste your text below, then press Enter twice when done:\n")
    
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    
    user_text = "\n".join(lines)
    
    if not user_text.strip():
        print("No text provided. Exiting.")
    else:
        print("\nSummarizing...\n")
        result = summarize_text(user_text)
        print(result)