"""O que cada teste do dbt confere, em palavras de quem lê a página (seção 4.3 "As execuções").

Os testes genéricos (vazio, repetido, valores aceitos, relação entre tabelas) ganham a frase pelo TIPO do teste, em `frase_generica`.
Os testes escritos à mão (dbt/tests/*.sql) precisam estar em `ESCRITOS_A_MAO`; **teste escrito à mão sem frase quebra o build**
(`execucoes.py` levanta erro, e a CI fica vermelha), assim a lista da página nunca fica com um teste sem explicação.
Cada tabela (seed, staging ou mart) que tem teste também precisa de um nome de leitor em `TABELAS`, na ordem em que aparece.

Os campos `achou` leem a linha que o teste devolve (o gerador roda a consulta compilada do próprio teste no DuckDB do build) e dizem o
que ele achou; só os testes que podem virar aviso precisam dele. `aviso` diz por que, quando cai, é aviso e não erro.
"""
from __future__ import annotations

from typing import Callable

ETAPAS = {"seed": "Listas de referência", "staging": "Entrada", "marts": "Tabelas finais"}

# tabela do dbt → (nome de leitor), na ordem em que os grupos aparecem em cada etapa
TABELAS: dict[str, str] = {
    "ats_hosts": "portais de vaga",
    "ferramentas": "lista de ferramentas",
    "lista_setores": "lista de setores",
    "niveis": "regras de nível",
    "taxonomia": "lista de itens",
    "stg_vagas": "as vagas",
    "stg_requisitos": "as linhas dos anúncios",
    "stg_benchmarks": "referências de salário",
    "stg_empresas": "empresas e setores",
    "stg_rotulos": "a classificação de cada linha",
    "stg_rotulo_itens": "itens marcados",
    "stg_rotulo_ferramentas": "ferramentas marcadas",
    "mart_vagas": "vagas com nível",
    "mart_vaga_item": "vaga × item",
    "mart_vaga_ferramenta": "vaga × ferramenta",
    "mart_repost": "anúncios repetidos",
    "mart_cobertura_rotulos": "cobertura da classificação",
}


def _fr(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _plural(n: int, um: str, varios: str) -> str:
    return f"{_fr(n)} {um if n == 1 else varios}"


def _achou_datas(linhas: list[dict]) -> str:
    """Vaga com data fora de ordem: quantas, e de quantos dias é o pior caso de cada tipo."""
    pub = [(l["data_publicacao"] - l["data_captura"]).days for l in linhas if l["data_publicacao"] and l["data_publicacao"] > l["data_captura"]]
    cap = [(l["data_analise"] - l["data_captura"]).days * -1 for l in linhas if l["data_captura"] > l["data_analise"]]
    partes = []
    if pub:
        ate = "" if len(pub) == 1 else "até "
        partes.append(f"<b>{_plural(len(pub), 'vaga', 'vagas')}</b> com data de publicação {ate}{max(pub)} dias depois do dia em que foi vista")
    if cap:
        ate = "" if len(cap) == 1 else "até "
        partes.append(f"<b>{_plural(len(cap), 'vaga', 'vagas')}</b> vista depois do dia da leitura ({ate}{max(cap)} dias)")
    return " · ".join(partes) + "." if partes else ""


def _achou_cobertura(linhas: list[dict]) -> str:
    l = linhas[0]
    pct = round(100 * l["rotuladas"] / l["linhas"]) if l["linhas"] else 0
    return f"<b>{_fr(int(l['rotuladas']))} de {_fr(int(l['linhas']))} linhas</b> ({pct}%)."


# nome do teste → tabela onde aparece, o que confere, por que é aviso (quando pode ser), o que achou (quando pode ser aviso)
ESCRITOS_A_MAO: dict[str, dict] = {
    "cobertura_minima_cidade": {"tabela": "mart_vagas", "frase": "cidade preenchida em vagas suficientes pra análise por local",
        "aviso": "Poucas cidades preenchidas limitam a leitura por local, mas não invalidam o resto."},
    "empresa_sem_setor": {"tabela": "stg_vagas", "frase": "toda empresa tem setor na lista de empresas",
        "aviso": "Empresa nova chega sem setor até a lista ser atualizada; a próxima publicação resolve."},
    "nivel_outros_alto": {"tabela": "mart_vagas", "frase": "no máximo 15% das vagas sem nível definido",
        "aviso": "Muita vaga sem nível pede revisão das regras de nível, mas a comparação continua valendo."},
    "requisitos_chave_unica": {"tabela": "stg_requisitos", "frase": "vaga + posição não se repetem (nem nas referências de salário)"},
    "rotulo_contexto_com_item": {"tabela": "stg_rotulos", "frase": "linha de contexto não carrega item"},
    "rotulo_linha_unica": {"tabela": "stg_rotulos", "frase": "cada linha é classificada uma vez"},
    "rotulo_setor_coerente": {"tabela": "lista_setores", "frase": "o setor marcado numa linha vem da lista fechada e só aparece junto do item de setor"},
    "rotulo_versao_unica": {"tabela": "stg_rotulos", "frase": "uma só versão da lista de itens no arquivo"},
    "rotulos_cobertura_baixa": {"tabela": "mart_cobertura_rotulos", "frase": "toda linha de anúncio já foi classificada",
        "aviso": "Classificação pela metade é o estado normal enquanto ela roda, e não pode deixar o build vermelho.",
        "achou": _achou_cobertura},
    "vaga_datas_coerentes": {"tabela": "stg_vagas", "frase": "as datas seguem a ordem natural: publicada, vista, lida",
        "aviso": "O anúncio pode trazer a data de uma republicação, e a leitura de uma vaga antiga pode ter sido refeita depois.",
        "achou": _achou_datas},
    "vaga_ferramenta_unico": {"tabela": "mart_vaga_ferramenta", "frase": "cada vaga × ferramenta aparece uma vez"},
    "vaga_item_unico": {"tabela": "mart_vaga_item", "frase": "cada vaga × item aparece uma vez"},
    "vaga_sem_requisito": {"tabela": "mart_vagas", "frase": "toda vaga tem pelo menos uma linha de requisito"},
}

AVISO_PADRAO = "Este teste está configurado como aviso: se cai, o build segue e a página é refeita."


def frase_generica(tipo: str, coluna: str | None, kwargs: dict) -> str | None:
    """Frase do teste genérico pelo tipo; `None` se o tipo não tem frase (o gerador então quebra o build)."""
    c = f"<code>{coluna}</code>"
    if tipo == "not_null":
        return f"{c} sempre tem valor"
    if tipo == "unique":
        return f"{c} não repete valor"
    if tipo == "accepted_values":
        vals = [str(v) for v in kwargs.get("values", [])]
        txt = ", ".join(vals) if len(vals) <= 6 else f"{', '.join(vals[:3])}, …, {', '.join(vals[-2:])} ({len(vals)} valores)"
        return f"{c} só assume: {txt}"
    if tipo == "relationships":
        destino = str(kwargs.get("to", "")).replace("ref('", "").replace("')", "").replace('ref("', "").replace('")', "")
        return f"todo {c} existe também em <code>{destino}.{kwargs.get('field')}</code>"
    return None


Achou = Callable[[list[dict]], str]
