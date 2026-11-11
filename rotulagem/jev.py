"""Rotula as linhas de uma amostra com o Jev (TypeSafe, "System One"), pela API da TypeSafe. Item 6.

    python rotulagem/jev.py contar --conjunto referencia --modelo jev-1.14.0
    python rotulagem/jev.py rodar  --conjunto pratica    --modelo jev-1.14.0 --max-usd 0.5
    python rotulagem/jev.py rodar  --conjunto referencia --modelo jev-1.14.0 --max-usd 0.5

O Jev não gera texto: responde perguntas tipadas (escolha numa lista fechada, sim/não) com probabilidade. Por isso a
adaptação, que entra no relatório como custo extra de usá-lo (os outros candidatos rotulam a vaga inteira numa chamada):

- uma requisição por **linha** (não por vaga). O `state` é a vaga inteira (as linhas numeradas, com a seção) e o número
  da linha em análise, pra ele ler a linha com o contexto das vizinhas;
- a `natureza` é uma pergunta de escolha (3 opções); cada item da taxonomia é uma pergunta **sim/não** (Noul) com a
  definição, a regra de borda e os exemplos do `taxonomia.md`; o setor é uma escolha na lista de setores, lida só se o
  item `experiencia.setor` ganhar sim. Tudo na mesma requisição (as perguntas rodam em paralelo);
- o item vale se a probabilidade de sim passa do limiar. Fica gravada a probabilidade de cada item, e o limiar é
  escolhido na **prática** (88 linhas), nunca na referência (`avaliar.py` faz isso);
- sem justificativa (o campo `motivo` fica vazio) e sem o texto do `outro`: o Jev só escolhe, não escreve. O item
  `outro` não é perguntado.

Saída no mesmo formato dos outros rotuladores, em rotulagem/saida/typesafe_<modelo>_<conjunto>.json, mais `probs`,
`natureza_prob` e `setor_prob` por linha. Chave: TYPESAFE_API_KEY no .env da raiz (gitignored).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import taxonomia
from common import (AMOSTRA, JEV_MODELOS, JEV_USD_POR_TOKEN, SAIDA, gasto_total, gravar_json, ler_json,
                    registrar_gasto_direto)
from rotular import setores

URL = "https://api.typesafe.ai/v1/systemone"
LIMIAR = 0.5  # padrão gravado em `itens`; avaliar.py reescolhe pelo desempenho na prática
CARACTERES_POR_TOKEN = 3.2
NATUREZA_CRITERIOS = {
    "responsabilidade": "o que a pessoa vai fazer no cargo (Liderar a estratégia de dados; Garantir a qualidade dos dados)",
    "requisito": "o que a pessoa precisa ter ou saber (SQL avançado; 5 anos liderando times; graduação em exatas)",
    "contexto": "a linha não pede nada: é nota, descrição da empresa, do time ou do projeto (Setor: varejo de moda, 145 anos)",
}


def pergunta_id(chave: str) -> str:
    return chave.replace(".", "__")


def perguntas() -> dict:
    qs: dict = {"natureza": {
        "type": "choice",
        "instructions": "Qual é a natureza da linha em análise da vaga?",
        "criteria": NATUREZA_CRITERIOS}}
    for it in taxonomia.itens():
        if it["chave"] == taxonomia.OUTRO:
            continue
        qs[pergunta_id(it["chave"])] = {
            "type": "noul",
            "instructions": f"A linha em análise da vaga cita {it['item'].lower()}: {it['definicao']}?",
            "criteria": {
                "true": f"A linha cita isso de forma explícita. Exemplos reais: {it['exemplos']}",
                "false": f"A linha não cita, ou cai na borda: {it['borda']}"}}
    qs["setor"] = {
        "type": "choice",
        "instructions": "Se a linha em análise pede experiência num setor, qual é o setor? Se não pede, escolha nenhum.",
        "criteria": {**{s: f"experiência no setor {s}" for s in setores()}, "nenhum": "a linha não pede experiência setorial"}}
    return qs


def estado(vaga: dict, linha: dict) -> dict:
    return {"vaga": [f"{l['ordem']}. [{l['secao']}] {l['texto']}" for l in vaga["linhas"]],
            "linha_em_analise": f"{linha['ordem']}. [{linha['secao']}] {linha['texto']}"}


def requisicao(vaga: dict, linha: dict, modelo: str) -> dict:
    return {"model": modelo, "state": estado(vaga, linha), "questions": perguntas()}


def chamar(vaga: dict, linha: dict, modelo: str):
    corpo = json.dumps(requisicao(vaga, linha, modelo)).encode()
    pedido = urllib.request.Request(URL, data=corpo, headers={
        "Authorization": "Bearer " + os.environ["TYPESAFE_API_KEY"], "Content-Type": "application/json"})
    t0 = time.monotonic()
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(pedido, timeout=60) as r:
                dados = json.load(r)
            dados["latencia_s"] = round(time.monotonic() - t0, 2)
            return dados
        except urllib.error.HTTPError as e:
            detalhe = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503) and tentativa < 2:
                time.sleep(2 * (tentativa + 1))
                continue
            return RuntimeError(f"HTTP {e.code}: {detalhe}")
        except Exception as e:  # rede: refaz na próxima rodada
            return e


def interpretar(resp: dict, limiar: float = LIMIAR) -> dict:
    a = resp["answers"]
    probs = {i["chave"]: a[pergunta_id(i["chave"])]["noul"] for i in taxonomia.itens() if i["chave"] != taxonomia.OUTRO}
    nat = a["natureza"]
    natureza = nat["choice"]
    itens = [] if natureza == "contexto" else [k for k, p in probs.items() if p >= limiar]
    setor = a["setor"]["choice"] if "experiencia.setor" in itens else "nenhum"
    return {"natureza": natureza, "itens": itens, "outro": "", "setor": setor, "motivo": "",
            "probs": {k: round(p, 3) for k, p in probs.items()}, "natureza_prob": round(nat["probabilities"][natureza], 3),
            "natureza_probs": {k: round(v, 3) for k, v in nat["probabilities"].items()},
            "setor_prob": round(a["setor"]["probabilities"][a["setor"]["choice"]], 3)}


def caminho(modelo: str, conjunto: str):
    return SAIDA / f"typesafe_{modelo}_{conjunto}.json"


def contar(conjunto: str, modelo: str) -> None:
    vagas = ler_json(AMOSTRA / f"{conjunto}.json")["vagas"]
    n = sum(len(v["linhas"]) for v in vagas)
    exemplo = vagas[0]
    tam = len(json.dumps(requisicao(exemplo, exemplo["linhas"][0], modelo), ensure_ascii=False)) / CARACTERES_POR_TOKEN
    total = tam * n
    print(f"{modelo}: {n} requisições (uma por linha), ~{tam:,.0f} tokens de entrada cada, ~{total:,.0f} no total; "
          f"custo ~US$ {total * JEV_USD_POR_TOKEN:.2f} (US$ 42 por bilhão de tokens de entrada, saída grátis; "
          f"estimativa pelo tamanho do texto). Já gasto na rotulagem: US$ {gasto_total():.2f}.")


def rodar(conjunto: str, modelo: str, max_usd: float, trabalhadores: int) -> None:
    vagas = ler_json(AMOSTRA / f"{conjunto}.json")["vagas"]
    destino = caminho(modelo, conjunto)
    versao = taxonomia.versao()
    feitas = ler_json(destino) if destino.exists() else {}
    if feitas and next(iter(feitas.values()))["versao_taxonomia"] != versao:
        sys.exit(f"{destino.name} foi rotulado em outra versão da taxonomia; mova o arquivo antes de rotular de novo.")
    if "TYPESAFE_API_KEY" not in os.environ:
        sys.exit("Falta TYPESAFE_API_KEY no .env da raiz do repo.")
    rodada = f"{conjunto}-typesafe_{modelo}-{versao}"
    gasto = 0.0
    for vaga in vagas:
        if vaga["id_publico"] in feitas:
            continue
        if gasto >= max_usd:
            print(f"Parado: US$ {gasto:.4f} gastos, trava de US$ {max_usd:.2f}.")
            break
        with ThreadPoolExecutor(max_workers=trabalhadores) as pool:
            respostas = list(pool.map(lambda l: chamar(vaga, l, modelo), vaga["linhas"]))
        erros = [r for r in respostas if isinstance(r, Exception)]
        for r in respostas:
            if not isinstance(r, Exception):
                gasto += registrar_gasto_direto(rodada, vaga["id_publico"], f"typesafe/{modelo}",
                                                r["usage"]["input_tokens"], r["usage"].get("output_tokens", 0),
                                                r["usage"]["input_tokens"] * JEV_USD_POR_TOKEN)
        if erros:
            print(f"  {vaga['id_publico']}: {len(erros)} de {len(respostas)} chamadas falharam, vaga não salva: {erros[0]!r}")
            continue
        linhas = []
        for linha, r in zip(vaga["linhas"], respostas):
            linhas.append({"ordem": linha["ordem"], **interpretar(r), "latencia_s": r["latencia_s"],
                           "servido_por": r["model"]})
        feitas[vaga["id_publico"]] = {
            "versao_taxonomia": versao, "rotulador": f"typesafe/{modelo}", "limiar": LIMIAR, "linhas": linhas,
            "uso": {"input_tokens": sum(r["usage"]["input_tokens"] for r in respostas),
                    "requisicoes": len(respostas)},
            "usd": round(sum(r["usage"]["input_tokens"] for r in respostas) * JEV_USD_POR_TOKEN, 4)}
        gravar_json(destino, feitas)
        print(f"  {vaga['id_publico']}: {len(respostas)} linhas, {feitas[vaga['id_publico']]['uso']['input_tokens']} "
              f"tokens, US$ {feitas[vaga['id_publico']]['usd']:.4f}; gasto US$ {gasto:.4f}")
    gravar_json(destino, feitas)
    print(f"US$ {gasto:.4f} nesta rodada; {len(feitas)} de {len(vagas)} vagas -> {destino}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("modo", choices=["contar", "rodar"])
    parser.add_argument("--conjunto", required=True, choices=["pratica", "referencia"])
    parser.add_argument("--modelo", required=True, choices=JEV_MODELOS)
    parser.add_argument("--trabalhadores", type=int, default=4, help="rodar: linhas ao mesmo tempo")
    parser.add_argument("--max-usd", type=float)
    args = parser.parse_args()
    if args.modo == "contar":
        contar(args.conjunto, args.modelo)
    else:
        if args.max_usd is None:
            sys.exit("rodar exige --max-usd.")
        SAIDA.mkdir(parents=True, exist_ok=True)
        rodar(args.conjunto, args.modelo, args.max_usd, args.trabalhadores)


if __name__ == "__main__":
    main()
