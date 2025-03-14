import os
import whisper
import ollama
import chromadb
import json
import numpy as np
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sentence_transformers import SentenceTransformer

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load Whisper ASR Model
asr_model = whisper.load_model("base")

# Load Embedding Model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
json_path = r'D:\llm\nlinkdata\nsummary_new.json'

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="transcripts")

# Function to index transcript from JSON file
def index_transcripts_from_json(json_path):
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    for entry in data:
        text = entry.get("summary", "") + " " + entry.get("detail_summary", "")
        recording_name = entry.get("recording_name", "Unknown")
        location = entry.get("url_location", "#")

        if not text.strip():
            continue  # Skip empty entries

        embedding = embedding_model.encode([text])[0].tolist()
        collection.add(
            ids=[recording_name],
            embeddings=[embedding],
            metadatas=[{"text": text, "recording_name": recording_name, "location": location}]
        )

index_transcripts_from_json(json_path)

# Function to search transcripts
def search_transcript(query):
    query_embedding = embedding_model.encode([query])[0].tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=1)

    if not results or not results.get("ids") or not results["ids"][0]:
        return None, None, None

    metadata = results.get("metadatas", [[]])[0]
    if not metadata or not metadata[0]:
        return None, None, None

    return metadata[0].get("text", ""), metadata[0].get("recording_name", ""), metadata[0].get("location", "")

# API Endpoint for Querying LLM (RAG-based Answer)
@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    query = data.get("query", "").strip()

    retrieved_text, recording_name, location = search_transcript(query)

    if not retrieved_text:
        return jsonify({"response": "I couldn't find anything relevant.", "source": "", "location": ""})

    # Use RAG to generate an answer, not copy full paragraphs
    response = ollama.chat(
        model="mistral",
        messages=[
            {"role": "system", "content": "You are an expert assistant. Answer questions concisely based only on the provided transcript."},
            {"role": "user", "content": f"Context: {retrieved_text}\n\nQuestion: {query}\n\nAnswer concisely and directly."}
        ]
    )

    if response is None or "message" not in response or "content" not in response["message"]:
        return jsonify({"response": "Error retrieving response from LLM.", "source": "", "location": ""})

    return jsonify({
        "response": response["message"]["content"].strip(),
        "source": recording_name,
        "location": location
    })

# API Endpoint to Display ChromaDB Content
@app.route("/list_data", methods=["GET"])
def list_data():
    results = collection.get()
    return jsonify(results)

# Web UI for Chatbot
@app.route("/")
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>NLink Chatbot</title>
        <script>
            async function askQuestion() {
                let query = document.getElementById("query").value;
                let response = await fetch("/ask", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({"query": query})
                });
                let data = await response.json();
                document.getElementById("response").innerHTML = `<strong>Response:</strong> ${data.response}<br><strong>Source:</strong> ${data.source}<br><strong>Location:</strong> <a href="${data.location}" target="_blank">${data.location}</a>`;
            }
        </script>
    </head>
    <body>
        <h2>Chatbot Interface</h2>
        <input type="text" id="query" placeholder="Enter your question...">
        <button onclick="askQuestion()">Ask</button>
        <p id="response"></p>
    </body>
    </html>
    '''

if __name__ == "__main__":
    app.run(debug=True)
