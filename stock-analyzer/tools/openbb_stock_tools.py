from langchain.tools import tool
from openbb import obb
from langchain_community.utilities.polygon import PolygonAPIWrapper
from langchain_community.tools.polygon import PolygonAggregates, PolygonTickerNews
import os
from datetime import datetime, timezone, timedelta
import requests
import json
from typing import Optional

POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY")
polygon_wrapper = PolygonAPIWrapper(api_key=POLYGON_API_KEY)

def resolve_ticker(symbol: str) -> str:
    """Resolve a company name or ticker to an official ticker symbol."""
    if symbol.isalpha() and 1 <= len(symbol) <= 5:
        return symbol.upper()
    
    try:
        results = obb.equity.search(query=symbol)
        df = results.to_df()
        if not df.empty:
            exact_matches = df[df['name'].str.contains(symbol, case=False)]
            if not exact_matches.empty:
                return exact_matches.iloc[0]['symbol']
            return df.iloc[0]['symbol']
    except Exception:
        pass
    return symbol.upper()

@tool
def get_company_name_from_ticker(ticker: str) -> str:
    """Lookup a company name for a ticker symbol. Input should be a ticker symbol like 'TSLA'."""
    try:
        symbol = resolve_ticker(ticker)
        result = obb.equity.profile(symbol=symbol)
        df = result.to_df()
        if df.empty:
            return f"No company found for ticker {ticker}"
        name = df.iloc[0].get("longName") or df.iloc[0].get("shortName")
        return name if name else f"Company name not available for {ticker}"
    except Exception as e:
        return f"Error looking up company name: {str(e)}"

@tool
def get_ticker_from_company_name(company_name: str) -> str:
    """Get the stock ticker symbol for a company name. Input should be a company name like 'Tesla'."""
    try:
        symbol = resolve_ticker(company_name)
        if symbol == company_name.upper() and len(symbol) > 5:
            return f"Could not find ticker for company: {company_name}"
        return f"The ticker symbol for {company_name} is {symbol}"
    except Exception as e:
        return f"Error finding ticker: {str(e)}"

@tool
def get_stock_summary(ticker: str) -> str:
    """Return a company profile summary for the given ticker symbol."""
    try:
        symbol = resolve_ticker(ticker)
        result = obb.equity.profile(symbol=symbol)
        df = result.to_df()
        if df.empty:
            return f"No summary available for {symbol}."
        name = df.iloc[0].get("longBusinessSummary", "No description available.")
        sector = df.iloc[0].get("sector", "Unknown")
        return f"{symbol} ({get_company_name_from_ticker(symbol)}) operates in {sector} sector. Description: {name}"
    except Exception as e:
        return f"Error retrieving summary: {str(e)}"

@tool
def get_stock_price(ticker: str) -> str:
    """Fetch the most recent closing stock price for a given ticker symbol."""
    try:
        symbol = resolve_ticker(ticker)
        response = obb.equity.price.historical(symbol=symbol)
        df = response.to_df()

        if df.empty:
            return f"No price data found for {symbol}."

        last_row = df.iloc[-1]
        date_str = last_row.name.strftime("%Y-%m-%d")
        close_price = last_row["close"]

        return (
            f"Latest price for {symbol} ({get_company_name_from_ticker(symbol)}):\n"
            f"- Date: {date_str}\n"
            f"- Close: ${close_price:,.2f}"
        )
    except Exception as e:
        return f"Error retrieving price: {str(e)}"

@tool
def get_stock_history(input_str: str) -> str:
    """
    Fetch price history for a stock. Input format: 
    "TICKER" or "TICKER,START_DATE,END_DATE". 
    Dates in YYYY-MM-DD format.
    """
    try:
        if "," in input_str:
            parts = [p.strip() for p in input_str.split(",")]
            ticker = resolve_ticker(parts[0])
            from_date = parts[1]
            to_date = parts[2]
        else:
            ticker = resolve_ticker(input_str)
            today = datetime.now(timezone.utc)
            past = today - timedelta(days=30)
            from_date = past.strftime("%Y-%m-%d")
            to_date = today.strftime("%Y-%m-%d")

        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{from_date}/{to_date}"
        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": 50,
            "apiKey": POLYGON_API_KEY,
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if "results" not in data or not data["results"]:
            return f"No data found for {ticker} between {from_date} and {to_date}."

        markdown_table = f"""
### 📊 Price History for {ticker} ({get_company_name_from_ticker(ticker)})
**Period:** {from_date} to {to_date}

| Date       | Open    | High    | Low     | Close   | Volume      |
|------------|---------|---------|---------|---------|-------------|
"""
        for r in data["results"]:
            dt = datetime.fromtimestamp(r["t"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            markdown_table += f"| {dt} | ${r['o']:.2f} | ${r['h']:.2f} | ${r['l']:.2f} | ${r['c']:.2f} | {int(r['v']):,} |\n"

        return markdown_table
    except Exception as e:
        return f"Error retrieving history: {str(e)}"

@tool
def get_stock_news(ticker: str) -> str:
    """
    Fetch latest news headlines and descriptions for a given ticker symbol.
    Input should be a stock ticker like 'TSLA'.
    """
    try:
        symbol = resolve_ticker(ticker)
        company_name = get_company_name_from_ticker(symbol)
        
        # Get the news articles
        news_tool = PolygonTickerNews(api_wrapper=polygon_wrapper)
        result = news_tool.run(symbol)

        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                return result.strip()

        articles = result.get("results", []) if isinstance(result, dict) else result
        if not articles:
            return f"No recent news found for {symbol} ({company_name})."

        formatted = [f"### 📰 Latest News for {symbol} ({company_name})\n"]
        
        for art in articles[:5]:  # Show top 5 articles
            headline = art.get("title", "No headline available")
            url = art.get("article_url", "")
            source = art.get("publisher", {}).get("name", "Unknown source")
            pub_date = art.get("published_utc", "N/A")
            description = art.get("description", "No description available")
            
            # Format date
            try:
                dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                pub_date = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass

            formatted.append(
                f"#### {headline}\n"
                f"- **Source:** {source}\n"
                f"- **Published:** {pub_date}\n"
                f"- **Description:** {description}\n"
                f"- [Read full article]({url})\n"
            )

        return "\n".join(formatted)
    except Exception as e:
        return f"Error fetching news for {ticker}: {str(e)}"