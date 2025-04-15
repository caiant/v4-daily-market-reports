# -*- coding: utf-8 -*-
"""Enhanced Market Report with Professional Formatting"""

import yfinance as yf
import pandas as pd
import yagmail
from datetime import datetime
import pytz
import requests
from bs4 import BeautifulSoup
import re

# Email credentials (use environment variables in production)
EMAIL_ADDRESS = "cailin.antonio@glccap.com"
EMAIL_PASSWORD = "ohdu zsxf lahi mpss"
TO_EMAILS = ["lovelycailin@gmail.com"]
BCC_EMAILS = "caiantonio2427@gmail.com"

# Updated and verified ticker symbols
tickers = {
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
    "SSE Composite": "000001.SS",
    "FTSE 100": "^FTSE",
    "DAX Index": "^GDAXI",
    "S&P 500 (prior day)": "^GSPC",
    "Dow Jones (prior day)": "^DJI",
    "Nasdaq Composite (prior day)": "^IXIC",
    "USD/JPY (Yen)": "JPY=X",
    "EUR/USD (Euro)": "EURUSD=X",
    "GBP/USD (Pound)": "GBPUSD=X",
    "Crude Oil (WTI)": "WTI",
    "S&P Futures": "ES=F",
    "Dow Jones Futures": "YM=F",
    "Nasdaq Futures": "NQ=F",
    "Gold Futures": "GC=F"
}

def get_trading_economics_yields():
    yields = {}
    urls = {
        "UK 10Y Gilt Yield": "https://tradingeconomics.com/united-kingdom/government-bond-yield",
        "Germany 10Y Bond Yield": "https://tradingeconomics.com/germany/government-bond-yield"
    }

    headers = {"User-Agent": "Mozilla/5.0"}

    for name, url in urls.items():
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            match = re.search(rf"{name.split()[0]} 10Y\s+([\d.]+)", text)
            if match:
                yields[name] = f"{match.group(1)}%"
            else:
                yields[name] = "Not found"
        except Exception as e:
            yields[name] = f"Error: {str(e)}"
    return yields

def get_market_data():
    """Fetch market data with enhanced error handling"""
    data = []
    for name, symbol in tickers.items():
        try:
            asset = yf.Ticker(symbol)
            info = asset.history(period="2d")
            
            if not info.empty and len(info) >= 2:
                last_close = info["Close"].iloc[-1]
                prev_close = info["Close"].iloc[-2]
                change = last_close - prev_close
                percent_change = (change / prev_close) * 100

                if "Yield" in name:
                    data.append([name, f"{last_close:.2f}%", f"{change:.2f}", f"{percent_change:.2f}%"])
                elif any(x in name for x in ["Nikkei", "Hang Seng", "FTSE", "DAX", "S&P", "Dow", "Nasdaq", "Gold"]):
                    data.append([name, f"{last_close:,.2f}", f"{change:,.2f}", f"{percent_change:.2f}%"])
                elif any(x in name for x in ["USD/JPY", "EUR/USD", "GBP/USD"]):
                    data.append([name, f"{last_close:.4f}", f"{change:.4f}", f"{percent_change:.2f}%"])
                else:
                    data.append([name, f"{last_close:.2f}", f"{change:.2f}", f"{percent_change:.2f}%"])
            else:
                data.append([name, "No Data", "N/A", "N/A"])
        except Exception as e:
            print(f"Error fetching {name}: {str(e)}")
            data.append([name, "Error", "Error", "Error"])

    bond_yields = get_trading_economics_yields()
    for name, value in bond_yields.items():
        data.append([name, value, "N/A", "N/A"])

    return pd.DataFrame(data, columns=["Asset", "Last Price", "Change", "Change %"])

def format_html_report(df):
    current_time = datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M %Z')

    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
            }}
            h2 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                box-shadow: 0 2px 3px rgba(0,0,0,0.1);
            }}
            th {{
                background-color: #3498db;
                color: white;
                text-align: center;
                padding: 12px;
                font-weight: bold;
            }}
            td {{
                padding: 10px;
                text-align: center;
                border-bottom: 1px solid #ddd;
            }}
            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            tr:hover {{
                background-color: #e9f7fe;
            }}
            .positive {{
                color: #27ae60;
                font-weight: bold;
            }}
            .negative {{
                color: #e74c3c;
                font-weight: bold;
            }}
            .footer {{
                font-size: 12px;
                color: #7f8c8d;
                text-align: center;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <h2>📈 Daily Market Report - {current_time}</h2>
        <table>
            <thead>
                <tr>
                    <th>Asset</th>
                    <th>Last Price</th>
                    <th>Change</th>
                    <th>Change %</th>
                </tr>
            </thead>
            <tbody>
    """

    for _, row in df.iterrows():
        change_class = ""
        try:
            if float(row['Change'].replace(',', '')) > 0:
                change_class = "positive"
            elif float(row['Change'].replace(',', '')) < 0:
                change_class = "negative"
        except:
            pass

        html += f"""
                <tr>
                    <td>{row['Asset']}</td>
                    <td>{row['Last Price']}</td>
                    <td class="{change_class}">{row['Change']}</td>
                    <td class="{change_class}">{row['Change %']}</td>
                </tr>
        """

    html += f"""
            </tbody>
        </table>
        <div class="footer">
            <p>Data source: Yahoo Finance | Report generated at {current_time}</p>
        </div>
    </body>
    </html>
    """
    return html

def send_email():
    try:
        df = get_market_data()
        report_html = format_html_report(df)
        subject = f"Daily Market Report - {datetime.now().strftime('%Y-%m-%d')}"

        yag = yagmail.SMTP(EMAIL_ADDRESS, EMAIL_PASSWORD)
        yag.send(
            to=TO_EMAILS,
            subject=subject,
            contents=report_html,
            bcc=BCC_EMAILS
        )
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")

if __name__ == "__main__":
    send_email()
