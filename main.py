from dotenv import load_dotenv
from langchain_agent import query_csv
load_dotenv()

if __name__ == "__main__":
    # Prompt for user question
    question = input("Ask a question about your cloud usage: ")

    # Prompt for CSV file path, or use default
    file_path = input("Enter the path to your CSV file [default: data/part5.csv]: ").strip()
    if not file_path:
        file_path = "data/part5.csv"

    response = query_csv(question, file_path)
    print("\nResponse:\n", response)
