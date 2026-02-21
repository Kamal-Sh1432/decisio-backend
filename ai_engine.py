import os
import json
import re
import pandas as pd
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def safe_json_extract(text: str):
    try:
        text = re.sub(r"```json", "", text)
        text = re.sub(r"```", "", text)

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))

        raise Exception("No JSON object found in AI response")

    except Exception as e:
        raise Exception(f"JSON Parsing Failed: {str(e)}")


def generate_analysis(df: pd.DataFrame, question: str):
    
    # ==============================
    # CLEAN NUMERIC COLUMNS
    # ==============================

    for col in ["Sales", "Profit"]:
        if col in df.columns:
            df[col] = (
            df[col]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ==============================
    # 1️⃣ REAL KPI CALCULATIONS
    # ==============================

    total_sales = float(df["Sales"].sum()) if "Sales" in df.columns else 0
    total_profit = float(df["Profit"].sum()) if "Profit" in df.columns else 0
    total_orders = (
        int(df["Order ID"].nunique())
        if "Order ID" in df.columns
        else len(df)
    )

    profit_margin = (
        round((total_profit / total_sales) * 100, 2)
        if total_sales > 0
        else 0
    )

    primary_kpis = [
        {"name": "Total Sales", "value": round(total_sales, 2)},
        {"name": "Total Orders", "value": total_orders},
        {"name": "Total Profit", "value": round(total_profit, 2)},
        {"name": "Profit Margin (%)", "value": profit_margin},
    ]

    # ==============================
    # 2️⃣ BUILD CHARTS FROM DATA
    # ==============================

    charts = []

    # 🔹 Bar Chart — Sales by Category
    if "Category" in df.columns and "Sales" in df.columns:
        category_sales = (
            df.groupby("Category")["Sales"]
            .sum()
            .reset_index()
        )

        charts.append({
            "type": "bar",
            "title": "Sales by Category",
            "data": [
                {
                    "category": row["Category"],
                    "value": float(row["Sales"])
                }
                for _, row in category_sales.iterrows()
            ]
        })

    # 🔹 Trend Chart — Monthly Sales
    if "Order Date" in df.columns and "Sales" in df.columns:
        df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

        monthly = (
            df.groupby(df["Order Date"].dt.strftime("%Y-%m"))["Sales"]
            .sum()
            .reset_index()
            .sort_values("Order Date")
        )

        charts.append({
            "type": "trend",
            "title": "Monthly Revenue Trend",
            "data": [
                {
                    "month": row["Order Date"],
                    "value": float(row["Sales"])
                }
                for _, row in monthly.iterrows()
            ]
        })

    # 🔹 Pie Chart — Sales by Segment
    if "Segment" in df.columns and "Sales" in df.columns:
        segment_sales = (
            df.groupby("Segment")["Sales"]
            .sum()
            .reset_index()
        )

        charts.append({
            "type": "pie",
            "title": "Sales Distribution by Segment",
            "data": [
                {
                    "name": row["Segment"],
                    "value": float(row["Sales"])
                }
                for _, row in segment_sales.iterrows()
            ]
        })

    # ==============================
    # 3️⃣ SEND ONLY SUMMARY TO AI
    # ==============================

    dataset_summary = f"""
    Total Sales: {round(total_sales, 2)}
    Total Profit: {round(total_profit, 2)}
    Total Orders: {total_orders}
    Profit Margin: {profit_margin}%

    Columns Available: {list(df.columns)}
    """

    prompt = f"""
You are a Senior Business Analyst with 20+ years experience.

Based ONLY on this dataset summary:

{dataset_summary}

Business Question:
{question}

Respond ONLY with valid JSON.

Structure:

{{
  "industry": "",
  "executive_summary": "",
  "key_insights": [
    {{"title": "", "analysis": ""}}
  ],
  "recommendations": [
    {{"strategy": "", "action": ""}}
  ]
}}

Rules:
- Executive summary must be 2–3 concise business lines.
- Provide 4–5 key insights.
- Provide 3–4 actionable recommendations.
- Do not fabricate numbers.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=600,
        response_format={"type": "json_object"}
    )

    ai_text = response.choices[0].message.content.strip()

    ai_output = safe_json_extract(ai_text)

    # ==============================
    # 4️⃣ MERGE REAL DATA + AI TEXT
    # ==============================

    final_output = {
        "industry": ai_output.get("industry", "General Business"),
        "executive_summary": ai_output.get("executive_summary", ""),
        "primary_kpis": primary_kpis,
        "executive_dashboard": {
            "charts": charts
        },
        "key_insights": ai_output.get("key_insights", []),
        "recommendations": ai_output.get("recommendations", [])
    }

    return final_output