import pandas as pd
import os
import re
from datetime import datetime
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_community.chat_models import AzureChatOpenAI  # updated per deprecation warning


def extract_date_filter(question: str):
    month_map = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5,
        'june': 6, 'july': 7, 'august': 8, 'september': 9,
        'october': 10, 'november': 11, 'december': 12
    }
    question_lower = question.lower()

    ym_match = re.search(r'(\d{4})[-/](\d{1,2})', question_lower)
    if ym_match:
        return int(ym_match.group(1)), int(ym_match.group(2))

    for month_name, month_num in month_map.items():
        if month_name in question_lower:
            year_match = re.search(r'(\d{4})', question_lower)
            year = int(year_match.group(1)) if year_match else None
            return year, month_num

    return None, None


def query_csv(question: str, csv_path: str = "data/vm_costs.csv") -> str:
    print(f"[INFO] Loading CSV file: {csv_path}")
    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except Exception as e:
        return f"[ERROR] Failed to load CSV: {str(e)}"

    print(f"[INFO] Loaded {len(df)} rows.")

    # Define resource-related keywords
    resource_keywords = [
        "vm", "virtual machine", "storage", "sql", "vnet", "arc", "container",
        "function", "resource group", "vpn", "disk", "network"
    ]
    question_lower = question.lower()
    keyword = next((kw for kw in resource_keywords if kw in question_lower or question_lower in kw), None)

    # Extract date filter
    year_filter, month_filter = extract_date_filter(question)

    # Columns to search
    filter_columns = ["resourceGroup", "resourceId", "meterCategory", "meterSubCategory, costInUsd"]

    # Apply keyword filter
    if keyword:
        mask = False
        for col in filter_columns:
            if col in df.columns:
                mask = mask | df[col].astype(str).str.lower().str.contains(keyword, na=False)
        filtered_df = df[mask]
        print(f"[INFO] Filtering by keyword '{keyword}' in columns {filter_columns}")
        print(f"[DEBUG] Rows after keyword filtering: {len(filtered_df)}")
    else:
        filtered_df = df.copy()
        print("[INFO] No keyword detected in question. Using entire dataframe.")

    # Apply date filter
    if year_filter and month_filter:
        date_col = next((col for col in df.columns if "date" in col.lower()), None)
        if date_col:
            filtered_df[date_col] = pd.to_datetime(filtered_df[date_col], errors='coerce')
            filtered_df = filtered_df[
                (filtered_df[date_col].dt.year == year_filter) &
                (filtered_df[date_col].dt.month == month_filter)
            ]
            print(f"[INFO] Filtering by date {year_filter}-{month_filter:02d} on '{date_col}'")
        else:
            print("[INFO] No date column found to apply date filter.")
    else:
        print("[INFO] No date filter extracted from question.")

    # Keep only relevant columns
    relevant_columns = [
        "resourceGroup",
        "resourceId",
        "meterCategory",
        "meterSubCategory",
        "meterRegion",
        "costInUsd",
        "costInBillingCurrency",
        "servicePeriodEndDate"
    ]
    filtered_df = filtered_df[[col for col in relevant_columns if col in filtered_df.columns]]
    print(f"[INFO] Filtered data has {len(filtered_df)} rows and {len(filtered_df.columns)} columns.")

    if filtered_df.empty:
        return "Sorry, no data matched your query after filtering."

    # Set up Azure OpenAI agent
    llm = AzureChatOpenAI(
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature=0,
    )

    agent = create_pandas_dataframe_agent(llm, filtered_df, verbose=True, allow_dangerous_code=True)
    return agent.run(question)