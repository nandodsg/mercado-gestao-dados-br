"""Encanamento comum dos scripts de rotulagem: chave, cliente do gateway, preço e registro de gasto.

A chave do Vercel AI Gateway (`AI_GATEWAY_API_KEY`) vem do `.env` da raiz do repo (gitignored), nunca da linha de
comando. Os modelos de outras empresas (Google, xAI) passam pelo gateway, que tem API compatível com a da OpenAI.
Toda chamada paga entra em rotulagem/gastos.csv (tokens e US$), pra o README dizer o gasto real.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
ROTULAGEM = RAIZ / "rotulagem"
AMOSTRA = ROTULAGEM / "amostra"
SAIDA = ROTULAGEM / "saida"
REFERENCIA = ROTULAGEM / "referencia"
GASTOS = ROTULAGEM / "gastos.csv"
GATEWAY_URL = "https://ai-gateway.vercel.sh/v1"

# US$ por milhão de tokens, preço regional dos EUA do gateway (o maior). Raciocínio é cobrado como saída.
PRECOS = {
    "google/gemini-4-argon": {"input": 2.20, "output": 11.00, "cache_read": 0.11},
    "spacexai/grok-4.7": {"input": 2.20, "output": 6.60, "cache_read": 0.55},
}
ROTULADORES_GATEWAY = sorted(PRECOS)
OPUS = "claude-opus-5-5"  # rotula na sessão do Claude Code (assinatura), sem passar pelo gateway

load_dotenv(RAIZ / ".env")  # sem override: o .env nunca troca uma variável já definida


def slug(modelo: str) -> str:
    return modelo.replace("/", "_")


def gateway_client():
    from openai import OpenAI

    if "AI_GATEWAY_API_KEY" not in os.environ:
        raise SystemExit("Falta AI_GATEWAY_API_KEY no .env da raiz do repo.")
    return OpenAI(api_key=os.environ["AI_GATEWAY_API_KEY"], base_url=GATEWAY_URL)


def tokens(usage) -> tuple[int, int, int]:
    """(entrada sem cache, saída, entrada de cache) de um objeto de uso no formato da OpenAI."""
    detalhes = getattr(usage, "prompt_tokens_details", None)
    cache = (getattr(detalhes, "cached_tokens", 0) or 0) if detalhes else 0
    return (usage.prompt_tokens or 0) - cache, usage.completion_tokens or 0, cache


def usd(modelo: str, usage) -> float:
    if getattr(usage, "cost", None) is not None:  # o gateway informa o que cobrou; vale mais que a tabela
        return float(usage.cost)
    p = PRECOS[modelo]
    i, o, c = tokens(usage)
    return (i * p["input"] + o * p["output"] + c * p["cache_read"]) / 1e6


def registrar_gasto(rodada: str, passo: str, modelo: str, usage) -> float:
    custo = usd(modelo, usage)
    novo = not GASTOS.exists()
    with GASTOS.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        if novo:
            w.writerow(["registrado_em_utc", "rodada", "passo", "modelo", "tokens_entrada", "tokens_saida",
                        "tokens_cache", "usd"])
        w.writerow([dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), rodada, passo, modelo,
                    *tokens(usage), f"{custo:.4f}"])
    return custo


def gasto_total() -> float:
    if not GASTOS.exists():
        return 0.0
    with GASTOS.open(encoding="utf-8") as f:
        return sum(float(r["usd"]) for r in csv.DictReader(f))


def ler_json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"))


def gravar_json(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
