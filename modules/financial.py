AFRICAN_CURRENCIES = {
    "Nigerian Naira": {"code": "NGN", "symbol": "\u20a6"},
    "Ghanaian Cedi": {"code": "GHS", "symbol": "GH\u20b5"},
    "South African Rand": {"code": "ZAR", "symbol": "R"},
    "CFA Franc (XOF)": {"code": "XOF", "symbol": "CFA"},
    "Kenyan Shilling": {"code": "KES", "symbol": "KSh"},
    "Egyptian Pound": {"code": "EGP", "symbol": "E\u00a3"},
    "Moroccan Dirham": {"code": "MAD", "symbol": "MAD"},
    "Tanzanian Shilling": {"code": "TZS", "symbol": "TSh"},
    "Ugandan Shilling": {"code": "UGX", "symbol": "USh"},
}


class FinancialAnalyzer:
    def __init__(self, revenue=0, cogs=0, opex=0, currency="Nigerian Naira"):
        self.revenue = revenue
        self.cogs = cogs
        self.opex = opex
        self.currency_name = currency
        self.currency_info = AFRICAN_CURRENCIES.get(currency, AFRICAN_CURRENCIES["Nigerian Naira"])

    @property
    def symbol(self):
        return self.currency_info["symbol"]

    @property
    def gross_profit(self):
        return self.revenue - self.cogs

    @property
    def net_profit(self):
        return self.gross_profit - self.opex

    @property
    def gross_margin(self):
        if self.revenue > 0:
            return (self.gross_profit / self.revenue) * 100
        return 0.0

    def get_metrics(self):
        return {
            "revenue": self.revenue,
            "cogs": self.cogs,
            "opex": self.opex,
            "gross_profit": self.gross_profit,
            "net_profit": self.net_profit,
            "gross_margin": self.gross_margin,
            "currency": self.currency_info,
        }

    def build_review_prompt(self):
        sym = self.symbol
        return (
            f"Revenue: {sym}{self.revenue:,}, COGS: {sym}{self.cogs:,}, "
            f"Operating Expenses: {sym}{self.opex:,}. "
            f"Gross Margin is {self.gross_margin:.1f}%, "
            f"Net Profit is {sym}{self.net_profit:,} ({self.currency_name}). "
            f"Give me 3 bulleted recommendations to optimize margins "
            f"considering the African {self.currency_name} market context."
        )
