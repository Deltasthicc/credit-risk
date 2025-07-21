import re
import json

def rag_summary_to_json(text: str) -> dict:
    fields = [
        "Revenue", "Net Income", "Total Assets", "Total Liabilities", "Equity",
        "Country", "Industry"
    ]
    
    data = {}
    structured_lines = []
    remaining_lines = []

    # Pre-split the text into lines
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]

    # Go through each line to find structured fields
    for line in lines:
        matched = False
        for field in fields:
            if line.lower().startswith(field.lower() + ":"):
                value = line.split(":", 1)[1].strip()
                cleaned_value = value.split("(")[0].strip()
                data[field.replace(" ", "_")] = cleaned_value
                structured_lines.append(line)
                matched = True
                break
        if not matched:
            remaining_lines.append(line)

    # Join leftover lines as basic_analysis
    data["basic_analysis"] = " ".join(remaining_lines)

    return data

# Example usage
rag_summary_path = "C:\\Users\\Akshita\\Desktop\\project\\output_data\\rag_summary.txt"
with open(rag_summary_path, "r", encoding="utf-8") as f:
    text = f.read()

summary_json = rag_summary_to_json(text)

# Save to file
output_path = rag_summary_path.replace(".txt", ".json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(summary_json, f, indent=4)

print(" Converted RAG summary to JSON")