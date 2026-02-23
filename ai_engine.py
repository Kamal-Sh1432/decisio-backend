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
    # KPI CALCULATIONS
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
    # CHARTS
    # ==============================

    charts = []

    if "Category" in df.columns and "Sales" in df.columns:
        category_sales = df.groupby("Category")["Sales"].sum().reset_index()

        charts.append({
            "type": "bar",
            "title": "Sales by Category",
            "data": [
                {"category": row["Category"], "value": float(row["Sales"])}
                for _, row in category_sales.iterrows()
            ]
        })

    if "Segment" in df.columns and "Sales" in df.columns:
        segment_sales = df.groupby("Segment")["Sales"].sum().reset_index()

        charts.append({
            "type": "pie",
            "title": "Sales Distribution by Segment",
            "data": [
                {"name": row["Segment"], "value": float(row["Sales"])}
                for _, row in segment_sales.iterrows()
            ]
        })

    # ==============================
    # STRUCTURAL INTELLIGENCE (JSON-BASED)
    # ==============================

    structure_signals = []

    if "Sales" in df.columns:

        for col in df.columns:

            if col == "Sales":
                continue

            if df[col].dtype == "object" or str(df[col].dtype) == "category":

                if 1 < df[col].nunique() <= 20:

                    dimension_sales = (
                        df.groupby(col)["Sales"]
                        .sum()
                        .sort_values(ascending=False)
                    )

                    if len(dimension_sales) > 1:

                        top_name = dimension_sales.index[0]
                        top_value = dimension_sales.iloc[0]
                        top_share = round((top_value / total_sales) * 100, 2)

                        bottom_name = dimension_sales.index[-1]
                        bottom_value = dimension_sales.iloc[-1]
                        bottom_share = round((bottom_value / total_sales) * 100, 2)

                        structure_signals.append({
                            "dimension": col,
                            "top_contributor": top_name,
                            "top_share_percent": top_share,
                            "lowest_contributor": bottom_name,
                            "lowest_share_percent": bottom_share,
                            "concentration_risk": top_share >= 50
                        })

    # ==============================
    # DATA PACKAGE FOR AI
    # ==============================

    dataset_summary = {
        "total_sales": round(total_sales, 2),
        "total_profit": round(total_profit, 2),
        "total_orders": total_orders,
        "profit_margin_percent": profit_margin,
        "structure_signals": structure_signals
    }

    prompt = f"""
You are a board-level executive strategy advisor.

Answer the user's question using ONLY the structured JSON data below.

Business Performance Data (JSON):
{json.dumps(dataset_summary, indent=2)}

User Question:
{question}

Return ONLY valid JSON in this structure:

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

STRICT REQUIREMENTS:

1. Executive Summary must be 3–4 strong board-ready sentences.
2. Provide exactly 4 key insights.
3. Each insight must be 3–4 full executive sentences.
4. Provide 3–4 strategic recommendations.
5. Each recommendation must contain 3–4 full sentences.
6. Use ONLY values provided in the JSON.
7. If concentration_risk is true, clearly identify the dimension and percentage.
8. No generic filler statements.
9. Directly answer the user’s question.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1200,
        response_format={"type": "json_object"}
    )

    ai_text = response.choices[0].message.content.strip()
    ai_output = safe_json_extract(ai_text)

    final_output = {
        "industry": ai_output.get("industry", "General Business"),
        "executive_summary": ai_output.get("executive_summary", ""),
        "primary_kpis": primary_kpis,
        "executive_dashboard": {"charts": charts},
        "key_insights": ai_output.get("key_insights", []),
        "recommendations": ai_output.get("recommendations", [])
    }

    return final_output