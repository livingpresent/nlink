import json
import re

def fix_json_format(input_file, output_file):
    try:
        # Read the input JSON file as raw text
        with open(input_file, "r", encoding="utf-8") as f:
            raw_content = f.read()
        
        # Fix invalid control characters
        raw_content = raw_content.replace("\x00", "")  # Remove null characters if any
        raw_content = re.sub(r"[\x01-\x1F\x7F]", " ", raw_content)  # Replace other control characters with space
        
        # Parse the cleaned JSON
        data = json.loads(raw_content)
        
        # Process each entry in the JSON file
        for entry in data:
            if "detail_summary" in entry:
                # Normalize newlines and remove extra spaces
                entry["detail_summary"] = re.sub(r"\s*\n\s*", "\\n", entry["detail_summary"]).strip()
            
        # Write the fixed JSON to a new file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"Successfully fixed and saved to {output_file}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Example usage
input_filename = r'c:\users\wwonganu\Downloads\git_\nsummary_16.json'
output_filename = "nsummary_16.json"
fix_json_format(input_filename, output_filename)
