import yfinance as yf
import pandas as pd
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# --------------------------------------------------
# CONFIGURAÇÕES
# --------------------------------------------------
EMAIL_SENDER = "seu_email@gmail.com"
EMAIL_PASSWORD = "sua_senha_de_app"   # senha de app do Gmail
EMAIL_RECEIVER = "seu_email@gmail.com"

SYMBOLS = ["BTC-USD", "ETH-USD", "XRP-USD"]

PERIOD = "5y"         # último período de 5 anos
INTERVAL = "1d"       # candles diários

RSI_WINDOW = 14
EMA_FAST = 50
EMA_SLOW = 200


# --------------------------------------------------
# FUNÇÕES DO BOT
# --------------------------------------------------

def enviar_email(subject, text):
    """Envio de email seguro via Gmail."""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = subject

        msg.attach(MIMEText(text, "plain"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

        print("Email enviado!")
    except Exception as e:
        print(f"Erro enviando email: {e}")


def calcular_indicadores(df):
    """Adiciona RSI + EMA50 + EMA200 ao dataframe."""
    df["EMA50"] = df["Close"].ewm(span=EMA_FAST, adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=EMA_SLOW, adjust=False).mean()

    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(RSI_WINDOW).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(RSI_WINDOW).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    return df


def gerar_sinal(df):
    # Pegar a última linha corretamente
    ultimo = df.iloc[-1]

    ema50 = float(ultimo["EMA50"])
    ema200 = float(ultimo["EMA200"])
    rsi = float(ultimo["RSI"])

    # Lógica de sinal
    if ema50 > ema200 and rsi < 30:
        return "🔵 COMPRA (tendência forte + RSI baixo)"

    if ema50 < ema200 and rsi > 70:
        return "🔴 VENDA (tendência de baixa + RSI alto)"

    return "⚪ Sem sinal claro"


# --------------------------------------------------
# EXECUÇÃO PRINCIPAL
# --------------------------------------------------

def processar_moeda(symbol):
    print(f"\n=== Baixando dados de {symbol} ===")

    df = yf.download(symbol, period=PERIOD, interval=INTERVAL)

    if df.empty:
        return f"{symbol}: Erro ao baixar dados"

    df = calcular_indicadores(df)
    sinal = gerar_sinal(df)

    ultimo_preco = df["Close"].iloc[-1]

    texto = (
        f"MOEDA: {symbol}\n"
        f"Preço atual: {ultimo_preco:.2f}\n"
        f"RSI: {df['RSI'].iloc[-1]:.2f}\n"
        f"EMA50: {df['EMA50'].iloc[-1]:.2f}\n"
        f"EMA200: {df['EMA200'].iloc[-1]:.2f}\n\n"
        f"SINAL: {sinal}\n"
        "---------------------------------------\n"
    )

    return texto


def main():
    print("Rodando bot...")

    resultados = ""

    for s in SYMBOLS:
        resultados += processar_moeda(s)

    enviar_email("📊 Relatório Cripto Automático", resultados)

    print("\n=== RELATÓRIO GERADO ===")
    print(resultados)


if __name__ == "__main__":
    main()
