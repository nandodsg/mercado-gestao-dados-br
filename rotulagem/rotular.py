"""Rotula as linhas de requisito de um conjunto de vagas com um modelo, uma chamada por vaga inteira.

    python rotulagem/rotular.py contar --conjunto pratica --modelo google/gemini-4-argon       # grátis: estimativa
    python rotulagem/rotular.py rodar  --conjunto pratica --modelo google/gemini-4-argon --max-usd 1   # pago
    python rotulagem/rotular.py validar --conjunto pratica --modelo claude-opus-5-5            # confere um arquivo

Os modelos de outras empresas passam pelo Vercel AI Gateway, cada um sem ver o rótulo do outro (mesmo prompt, mesmo
esquema, mesma vaga). O Opus rotula na sessão do Claude Code e grava o arquivo no mesmo formato; `validar` confere.
`contar` estima o custo sem chamar nada (tamanho do texto em caracteres, ~3,2 por token: aproximado); `rodar` exige
`--max-usd`, para de começar chamadas ao passar dele e pula as vagas já rotuladas. Saída: rotulagem/saida/<modelo>_<conjunto>.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor

import taxonomia
from common import (AMOSTRA, OPUS, PRECOS, ROTULADORES_GATEWAY, SAIDA, RAIZ, gasto_total, gateway_client, gravar_json,
                    ler_json, registrar_gasto, slug)

ESFORCO = "medium"
MAX_TOKENS = 16000  # por chamada, raciocínio incluído: o teto duro por trás do custo no pior caso
CARACTERES_POR_TOKEN = 3.2
SAIDA_ESPERADA = 5000  # tokens de saída por vaga (raciocínio + rótulos + motivos): palpite pra estimativa


def setores() -> list[str]:
    with (RAIZ / "dbt" / "seeds" / "setores.csv").open(encoding="utf-8") as f:
        return sorted({r["setor"] for r in csv.DictReader(f)})


def prompt_sistema() -> str:
    modelo = (taxonomia.ARQUIVO.parent / "prompt.md").read_text(encoding="utf-8")
    return (modelo.replace("{setores}", "\n".join(f"- {s}" for s in setores()))
            .replace("{taxonomia}", taxonomia.texto()))


def render_vaga(vaga: dict) -> str:
    linhas = "\n".join(f"{l['ordem']}. {l['texto']}" for l in vaga["linhas"])
    return f"A vaga tem {len(vaga['linhas'])} linhas de requisito:\n\n{linhas}"


def esquema() -> dict:
    return {
        "type": "object",
        "properties": {"linhas": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "ordem": {"type": "integer"},
                "natureza": {"type": "string", "enum": taxonomia.NATUREZA},
                "itens": {"type": "array", "items": {"type": "string", "enum": taxonomia.chaves()}},
                "outro": {"type": "string"},
                "setor": {"type": "string", "enum": [*setores(), "nenhum"]},
                "motivo": {"type": "string"},
            },
            "required": ["ordem", "natureza", "itens", "outro", "setor", "motivo"],
            "additionalProperties": False}}},
        "required": ["linhas"],
        "additionalProperties": False,
    }


def requisicao(vaga: dict, modelo: str) -> dict:
    return {
        "model": modelo,
        "messages": [{"role": "system", "content": prompt_sistema()}, {"role": "user", "content": render_vaga(vaga)}],
        "response_format": {"type": "json_schema", "json_schema": {"name": "rotulos", "strict": True,
                                                                     "schema": esquema()}},
        "max_tokens": MAX_TOKENS,
        "extra_body": {"reasoning": {"effort": ESFORCO}},
    }


def validar_resultado(resultado: dict, vaga: dict) -> None:
    """Cada linha da vaga rotulada uma vez; natureza, itens e setor dentro da lista fechada."""
    chaves, ordens = set(taxonomia.chaves()), [l["ordem"] for l in vaga["linhas"]]
    recebidas = [l["ordem"] for l in resultado["linhas"]]
    if recebidas != ordens:
        raise ValueError(f"linhas {recebidas} não batem com as da vaga {ordens}")
    for l in resultado["linhas"]:
        if l["natureza"] not in taxonomia.NATUREZA:
            raise ValueError(f"linha {l['ordem']}: natureza {l['natureza']!r} fora da lista")
        if not set(l["itens"]) <= chaves:
            raise ValueError(f"linha {l['ordem']}: item fora da taxonomia: {sorted(set(l['itens']) - chaves)}")
        if l["natureza"] == "contexto" and l["itens"]:
            raise ValueError(f"linha {l['ordem']}: contexto não leva item")
        if ("outro" in l["itens"]) != bool(l["outro"].strip()):
            raise ValueError(f"linha {l['ordem']}: `outro` e o texto do outro precisam andar juntos")
        if l["setor"] not in [*setores(), "nenhum"] or (l["setor"] != "nenhum") != ("experiencia.setor" in l["itens"]):
            raise ValueError(f"linha {l['ordem']}: setor {l['setor']!r} não combina com os itens")


def analisar(texto: str) -> dict:
    texto = texto.strip()
    if texto.startswith("```"):  # alguns provedores embrulham o JSON em cerca de código mesmo com esquema
        texto = texto.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(texto)


def caminho(modelo: str, conjunto: str):
    return SAIDA / f"{slug(modelo)}_{conjunto}.json"


def contar(conjunto: str, modelo: str) -> None:
    vagas = ler_json(AMOSTRA / f"{conjunto}.json")["vagas"]
    preco = PRECOS[modelo]
    entrada = sum((len(prompt_sistema()) + len(render_vaga(v))) / CARACTERES_POR_TOKEN for v in vagas)
    n = len(vagas)
    esperado = (entrada * preco["input"] + SAIDA_ESPERADA * n * preco["output"]) / 1e6
    teto = (entrada * preco["input"] + MAX_TOKENS * n * preco["output"]) / 1e6
    print(f"{modelo}, esforço {ESFORCO}: {n} chamadas, ~{entrada:,.0f} tokens de entrada no total "
          f"(~{entrada / n:,.0f} por chamada; contagem aproximada pelo tamanho do texto)")
    print(f"Custo esperado ~US$ {esperado:.2f}; teto US$ {teto:.2f} (toda chamada no max_tokens={MAX_TOKENS:,}). "
          f"Já gasto na rotulagem: US$ {gasto_total():.2f}.")


def chamar(cliente, vaga: dict, modelo: str):
    try:
        r = cliente.chat.completions.create(**requisicao(vaga, modelo))
        return r
    except Exception as e:  # uma chamada que falha não derruba a rodada; ela é refeita na próxima
        return e


def rodar(conjunto: str, modelo: str, max_usd: float, trabalhadores: int) -> None:
    vagas = ler_json(AMOSTRA / f"{conjunto}.json")["vagas"]
    destino = caminho(modelo, conjunto)
    feitas = ler_json(destino) if destino.exists() else {}
    versao = taxonomia.versao()
    if feitas and next(iter(feitas.values()))["versao_taxonomia"] != versao:
        sys.exit(f"{destino.name} foi rotulado em outra versão da taxonomia; mova o arquivo antes de rotular de novo.")
    cliente = gateway_client()
    rodada = f"{conjunto}-{slug(modelo)}-{versao}"
    gasto = 0.0
    pendentes = [v for v in vagas if v["id_publico"] not in feitas]
    with ThreadPoolExecutor(max_workers=trabalhadores) as pool:
        for ini in range(0, len(pendentes), trabalhadores):
            if gasto >= max_usd:
                print(f"Parado: US$ {gasto:.2f} gastos, trava de US$ {max_usd:.2f}.")
                break
            lote = pendentes[ini:ini + trabalhadores]
            for vaga, saida in zip(lote, pool.map(lambda v: chamar(cliente, v, modelo), lote)):
                if isinstance(saida, Exception):
                    print(f"  {vaga['id_publico']}: chamada falhou, não salva: {saida!r}")
                    continue
                escolha = saida.choices[0]
                custo = registrar_gasto(rodada, vaga["id_publico"], modelo, saida.usage)
                gasto += custo
                print(f"  {vaga['id_publico']}: {saida.usage.prompt_tokens} entrada, {saida.usage.completion_tokens} "
                      f"saída, US$ {custo:.4f}, fim {escolha.finish_reason}; gasto US$ {gasto:.2f}")
                if escolha.finish_reason != "stop":
                    print(f"    não salva: parou com {escolha.finish_reason}")
                    continue
                try:
                    resultado = analisar(escolha.message.content or "")
                    validar_resultado(resultado, vaga)
                except (ValueError, KeyError, json.JSONDecodeError) as e:
                    print(f"    não salva: {e}")
                    continue
                feitas[vaga["id_publico"]] = {
                    "versao_taxonomia": versao, "rotulador": modelo, "servido_por": saida.model or modelo,
                    "esforco": ESFORCO, "usd": round(custo, 4), "uso": saida.usage.model_dump(), **resultado}
            gravar_json(destino, feitas)
    gravar_json(destino, feitas)
    print(f"US$ {gasto:.2f} nesta rodada (US$ {gasto_total():.2f} no total da rotulagem); "
          f"{len(feitas)} de {len(vagas)} vagas rotuladas -> {destino}")


def validar(conjunto: str, modelo: str) -> None:
    vagas = {v["id_publico"]: v for v in ler_json(AMOSTRA / f"{conjunto}.json")["vagas"]}
    feitas = ler_json(caminho(modelo, conjunto))
    versao = taxonomia.versao()
    ruins = 0
    for id_publico, vaga in vagas.items():
        r = feitas.get(id_publico)
        if r is None:
            print(f"  {id_publico}: sem rótulo")
            ruins += 1
            continue
        try:
            validar_resultado(r, vaga)
            if r.get("versao_taxonomia") != versao:
                raise ValueError(f"versao_taxonomia {r.get('versao_taxonomia')} != {versao}")
        except ValueError as e:
            print(f"  {id_publico}: {e}")
            ruins += 1
    print(f"{len(vagas) - ruins} de {len(vagas)} vagas válidas em {caminho(modelo, conjunto).name}")
    sys.exit(1 if ruins else 0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("modo", choices=["contar", "rodar", "validar"])
    parser.add_argument("--conjunto", required=True, choices=["pratica", "referencia"])
    parser.add_argument("--modelo", required=True, choices=[*ROTULADORES_GATEWAY, OPUS])
    parser.add_argument("--trabalhadores", type=int, default=1, help="rodar: chamadas ao mesmo tempo")
    parser.add_argument("--max-usd", type=float, help="rodar: para de começar chamadas ao passar disso")
    args = parser.parse_args()
    if args.modo == "validar":
        validar(args.conjunto, args.modelo)
    elif args.modelo == OPUS:
        sys.exit("O Opus rotula na sessão do Claude Code, não pelo gateway: use `validar` no arquivo dele.")
    elif args.modo == "contar":
        contar(args.conjunto, args.modelo)
    else:
        if args.max_usd is None:
            sys.exit("rodar exige --max-usd (a trava de gasto aprovada).")
        SAIDA.mkdir(parents=True, exist_ok=True)
        rodar(args.conjunto, args.modelo, args.max_usd, args.trabalhadores)


if __name__ == "__main__":
    main()
