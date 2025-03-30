from flask import Flask, request, jsonify
import os
import json
import ollama

app = Flask(__name__)

# Load all chunks into memory from JSON files
CHUNKS_DIR = "./chunked_json"
all_chunks = []

for fname in os.listdir(CHUNKS_DIR):
    if fname.endswith(".json"):
        with open(os.path.join(CHUNKS_DIR, fname), "r", encoding="utf-8") as f:
            all_chunks.extend(json.load(f))

@app.route("/ask_cag", methods=["POST"])
def ask_cag():
    data = request.json
    query = data.get("query", "").strip()

    # Concatenate all summaries into context
    context_parts = []
    for chunk in all_chunks:
        summary = chunk.get("summary", {}).get("brief_takeaway", "")
        recording = chunk.get("recording_name", "Unknown")
        presenter = chunk.get("presenter", "Unknown")
        time = chunk.get("timestamp", "")
        if summary:
            context_parts.append(f"[{recording}] by {presenter} at {time}:\n{summary}")

    full_context = "\n\n".join(context_parts)

    # Send to LLM via Ollama
    response = ollama.chat(
        model="mixtral",
        messages=[
            {
                "role": "system",
                "content": "You are a technical assistant. Use the provided context to answer the user's question. Be concise and include the recording name and presenter when relevant."
            },
            {
                "role": "user",
                "content": f"Context:\n{full_context}\n\nQuestion: {query}"
            }
        ]
    )

    answer = response["message"]["content"]
    return jsonify({
        "response": answer.strip()
    })

if __name__ == "__main__":
    app.run(debug=True, port=5001)
