import os
import json
import re
import ollama
from datetime import timedelta

# === CONFIGURATION ===
VTT_FOLDER = "./vtt"
OUTPUT_FOLDER = "./chunked_json"
CHUNK_DURATION = 90  # seconds per chunk
MODEL_NAME = "mistral"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === UTILITY FUNCTIONS ===
def parse_vtt(vtt_path):
    with open(vtt_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    entries = []
    start, end, text = None, None, []
    for line in lines:
        line = line.strip()
        if "-->" in line:
            if start and text:
                entries.append((start, end, " ".join(text)))
                text = []
            times = re.findall(r"(\d{2}:\d{2}:\d{2}\.\d{3})", line)
            if len(times) == 2:
                start, end = times
        elif line and not line.startswith("WEBVTT"):
            text.append(line)

    if start and text:
        entries.append((start, end, " ".join(text)))
    return entries

def time_to_seconds(ts):
    h, m, s = ts.split(":")
    s, ms = s.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s)

def seconds_to_time(sec):
    return str(timedelta(seconds=sec))

def chunk_entries(entries, chunk_duration=CHUNK_DURATION):
    chunks = []
    current_chunk, current_start, current_end = [], None, None
    chunk_id = 1

    for start, end, text in entries:
        start_sec = time_to_seconds(start)
        end_sec = time_to_seconds(end)

        if current_start is None:
            current_start = start_sec

        current_chunk.append(text)
        current_end = end_sec

        if current_end - current_start >= chunk_duration:
            chunks.append({
                "chunk_id": chunk_id,
                "start": seconds_to_time(current_start),
                "end": seconds_to_time(current_end),
                "text": " ".join(current_chunk)
            })
            chunk_id += 1
            current_chunk = []
            current_start, current_end = None, None

    if current_chunk:
        chunks.append({
            "chunk_id": chunk_id,
            "start": seconds_to_time(current_start),
            "end": seconds_to_time(current_end),
            "text": " ".join(current_chunk)
        })

    return chunks

def generate_prompt(transcript_chunk, start, end):
    return f"""
You are an AI assistant specialized in extracting and summarizing technical knowledge from audio recordings. Your task is to analyze the following transcript segment and return ONLY a JSON object with clearly structured outputs.

Output this format:

{{
  "detailed_extraction": {{
    "key_topics": [],
    "definitions_and_concepts": [],
    "processes_and_methodologies": [],
    "tools_and_technologies": [],
    "technical_insights_and_best_practices": [],
    "metrics_or_parameters": [],
    "decision_criteria_or_reasoning": []
  }},
  "summary": {{
    "main_point": "",
    "tools_or_methods": "",
    "key_recommendations": "",
    "brief_takeaway": ""
  }},
  "tags": [],
  "presenter": "Unknown",
  "timestamp": "{start} - {end}"
}}

Transcript:
\"\"\"
{transcript_chunk}
\"\"\"
"""

def process_vtt_file(vtt_path):
    base_name = os.path.splitext(os.path.basename(vtt_path))[0]
    entries = parse_vtt(vtt_path)
    chunks = chunk_entries(entries)

    output_chunks = []

    for chunk in chunks:
        prompt = generate_prompt(chunk["text"], chunk["start"], chunk["end"])
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        try:
            content = response["message"]["content"]
            json_data = json.loads(content)
            json_data["chunk_id"] = chunk["chunk_id"]
            json_data["recording_name"] = base_name
            json_data["start"] = chunk["start"]
            json_data["end"] = chunk["end"]
            output_chunks.append(json_data)
        except Exception as e:
            print(f"Error in chunk {chunk['chunk_id']} of {base_name}: {e}")

    output_path = os.path.join(OUTPUT_FOLDER, f"{base_name}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_chunks, f, indent=2)

    print(f"✅ Processed: {base_name}")

# Run on all VTT files
for fname in os.listdir(VTT_FOLDER):
    if fname.lower().endswith(".vtt"):
        process_vtt_file(os.path.join(VTT_FOLDER, fname))
