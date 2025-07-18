from flask import Flask, request, render_template, jsonify
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import pandas as pd
import torch
import sqlite3
import os

app = Flask(__name__, static_folder="static", template_folder="templates")

#  Load the model
model_path = "model/checkpoint-114070"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

#  Load data from CSV into SQLite
csv_path = "data/jamalon_dataset.csv"
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"? CSV file not found at {csv_path}")

#  Load and clean CSV before writing to SQLite
df = pd.read_csv(csv_path)

#  Normalize function for Arabic text
def clean_text(series):
    return (
        series.astype(str)
        .str.replace('�', '�')
        .str.replace('�', '�')
        .str.replace('�', '�')  
        .str.replace('�', '"')
        .str.replace('�', '"')
        .str.replace("�", "'")
        .str.replace("�", "'")
        .str.replace('\u200f', '')  # remove RTL markers
        .str.replace('\u200e', '')  # remove LTR markers
        .str.strip()
    )

# Clean key columns
for col in ['Title', 'Publisher', 'Category', 'Subcategory', 'Description']:
    if col in df.columns:
        df[col] = clean_text(df[col])

# Save cleaned data into SQLite
conn = sqlite3.connect("books.db", check_same_thread=False)
df.to_sql("books", conn, index=False, if_exists="replace")

# Generate SQL from input question
def generate_sql(question):
    print("?? Question:", question)
    inputs = tokenizer(question, return_tensors="pt", truncation=True, padding=True, max_length=128)
    with torch.no_grad():
        output_ids = model.generate(**inputs, max_length=128)
    sql = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    sql = sql.replace("�", "'").replace("�", "'")  # fix curved quotes
    print("?? Generated SQL:", sql)
    return sql.strip()

def execute_sql(sql):
    print("?? Running SQL:", sql)
    try:
        result = pd.read_sql_query(sql, conn)
        print("? Results:", len(result))
        if len(result) > 0:
            return result.to_dict(orient="records")

        if "WHERE" in sql:
            fallback_sql = sql
            conditions = fallback_sql.split("WHERE", 1)[1]
            for part in conditions.split("AND"):
                if "=" in part:
                    field, value = part.split("=", 1)
                    field = field.strip()
                    value = value.strip().strip(";").strip("'").strip('"')
                    fallback_sql = fallback_sql.replace(
                        f"{field} = '{value}'",
                        f"{field} LIKE '%{value}%'"
                    )

            print("?? Trying fallback SQL:", fallback_sql)
            result = pd.read_sql_query(fallback_sql, conn)
            print("? Fallback Results:", len(result))
            return result.to_dict(orient="records")

        return []
    except Exception as e:
        print("? SQL Error:", e)
        return {"error": str(e)}

# Web routes
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    question = request.json.get("question", "")
    sql = generate_sql(question)
    result = execute_sql(sql)
    return jsonify({"sql": sql, "result": result})

@app.route("/test-db")
def test_db():
    try:
        result = pd.read_sql_query("SELECT * FROM books LIMIT 5", conn)
        return result.to_html()
    except Exception as e:
        return f"<pre>? DB Error: {str(e)}</pre>"

if __name__ == "__main__":
    app.run(debug=True)

#pip install -r requirements.txt
# To run the app, use the command:
# python app.py