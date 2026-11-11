"""Exemplo: rotular as linhas de uma vaga com o Haiku 5.5 pelo Vercel AI Gateway (rota alternativa, não usada em produção).

A classificação de requisitos deste projeto roda pela assinatura do autor (cota semanal do Claude), não por API paga:
ver "Classificação de requisitos" no README e `PLAN.md`. Este arquivo mostra que a mesma tarefa roda por um gateway,
com o mesmo prompt, o mesmo esquema e a mesma validação, caso alguém queira reproduzir o trabalho ou o autor mude de rota.

    pip install openai python-dotenv
    export AI_GATEWAY_API_KEY=...            # ou no .env da raiz (gitignored)
    python pipeline/exemplo_gateway.py                        # primeira vaga da amostra de referência
    python pipeline/exemplo_gateway.py --vaga <id_publico> --modelo anthropic/claude-haiku-5.5

Custo de referência medido em `evals/relatorio.md`: centavos por mil linhas. O gateway informa o que cobrou em
`usage.cost`; o script imprime esse valor. Não grava nada em disco.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "rotulagem"))

import rotular  # noqa: E402  (prompt, esquema e validação do projeto)
from common import AMOSTRA, GATEWAY_URL, ler_json  # noqa: E402

MODELO_PADRAO = "anthropic/claude-haiku-5.5"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--vaga", help="id_publico de uma vaga da amostra de referência (padrão: a primeira)")
    parser.add_argument("--modelo", default=MODELO_PADRAO)
    args = parser.parse_args()
    if "AI_GATEWAY_API_KEY" not in os.environ:
        sys.exit("Falta AI_GATEWAY_API_KEY.")

    from openai import OpenAI  # o gateway fala o protocolo da OpenAI

    vagas = ler_json(AMOSTRA / "referencia.json")["vagas"]
    vaga = next((v for v in vagas if v["id_publico"] == args.vaga), vagas[0]) if args.vaga else vagas[0]

    cliente = OpenAI(api_key=os.environ["AI_GATEWAY_API_KEY"], base_url=GATEWAY_URL)
    resposta = cliente.chat.completions.create(**rotular.requisicao(vaga, args.modelo))
    escolha = resposta.choices[0]
    if escolha.finish_reason != "stop":
        sys.exit(f"Resposta incompleta: {escolha.finish_reason}")

    resultado = rotular.analisar(escolha.message.content or "")
    rotular.reparar(resultado)  # só incoerência de forma entre campos; o julgamento não muda
    rotular.validar_resultado(resultado, vaga)  # lista fechada, uma linha rotulada uma vez

    for linha in resultado["linhas"][:5]:
        print(linha["ordem"], linha["natureza"], linha["itens"])
    custo = getattr(resposta.usage, "cost", None)
    print(f"... {len(resultado['linhas'])} linhas; {resposta.usage.prompt_tokens} tokens de entrada, "
          f"{resposta.usage.completion_tokens} de saída; custo US$ {custo if custo is not None else 'não informado'}")


if __name__ == "__main__":
    main()
