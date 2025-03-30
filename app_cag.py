from flask import Flask, request, jsonify, render_template
import os
import json
import ollama
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# === Load All Summaries from Chunked JSON Files ===
CHUNKS_DIR = "./chunked_json"
all_chunks = []

for fname in os.listdir(CHUNKS_DIR):
    if fname.endswith(".json"):
        with open(os.path.join(CHUNKS_DIR, fname), "r", encoding="utf-8") as f:
            all_chunks.extend(json.load(f))

# === CAG-Based QA Endpoint ===
@app.route("/ask_cag", methods=["POST"])
def ask_cag():
    data = request.json
    query = data.get("query", "").strip()

    # Build context from all chunks
    context_parts = []
    for chunk in all_chunks:
        summary = chunk.get("summary", {}).get("brief_takeaway", "")
        recording = chunk.get("recording_name", "Unknown")
        presenter = chunk.get("presenter", "Unknown")
        timestamp = chunk.get("timestamp", "")

        if summary:
            context_parts.append(f"[{recording}] by {presenter} at {timestamp}:
{summary}")

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

    answer = response["message"]["content"].strip()
    return jsonify({
        "response": answer
    })

# === Simple Web UI ===
@app.route("/")
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>CAG Chatbot</title>
        <script>
            async function askQuestion() {
                let query = document.getElementById("query").value;
                let response = await fetch("/ask_cag", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({"query": query})
                });
                let data = await response.json();
                document.getElementById("response").innerHTML = `<strong>Response:</strong> ${data.response}`;
            }
        </script>
    </head>
    <body>
        <h2>CAG Chatbot</h2>
        <input type="text" id="query" placeholder="Enter your question..." size="60">
        <button onclick="askQuestion()">Ask</button>
        <p id="response"></p>
    </body>
    </html>
    '''

if __name__ == "__main__":
    app.run(debug=True, port=5001)
