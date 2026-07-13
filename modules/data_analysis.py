import pandas as pd


class DataAnalyzer:
    def __init__(self, df):
        self.df = df

    def preview(self, n=5):
        return self.df.head(n)

    def summary_text(self):
        return (
            f"Columns: {list(self.df.columns)}\n"
            f"Types:\n{self.df.dtypes.to_string()}\n"
            f"Describe:\n{self.df.describe().to_string()}"
        )

    def rich_context(self, max_rows=10):
        sample = self.df.head(max_rows).to_string(index=False)
        return (
            f"Dataset: {self.df.shape[0]} rows x {self.df.shape[1]} columns\n"
            f"Columns: {list(self.df.columns)}\n"
            f"Types:\n{self.df.dtypes.to_string()}\n"
            f"First {min(max_rows, self.df.shape[0])} rows:\n{sample}\n\n"
            f"Stats:\n{self.df.describe().to_string()}"
        )

    def numeric_columns(self):
        return self.df.select_dtypes(include=["number"]).columns.tolist()

    def all_columns(self):
        return self.df.columns.tolist()

    @staticmethod
    def read_csv(file):
        return pd.read_csv(file)

    @staticmethod
    def build_insight_prompt(context, goal):
        return (
            f"Here is the actual dataset:\n{context}\n\n"
            f"User question: {goal}\n\n"
            f"Answer with specific numbers from the data above. Be concise."
        )
