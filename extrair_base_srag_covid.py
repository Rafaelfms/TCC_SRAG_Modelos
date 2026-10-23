import sys
import argparse
import traceback
from pathlib import Path
import pandas as pd

COLUNAS = [
    "NU_NOTIFIC", "DT_NOTIFIC", "DT_SIN_PRI", "DT_INTERNA",
    "NU_IDADE_N", "TP_IDADE", "CS_SEXO", "CS_RACA", "CS_GESTANT", "SG_UF", "CS_ZONA",
    "FEBRE", "TOSSE", "GARGANTA", "DISPNEIA", "DESC_RESP", "SATURACAO",
    "DIARREIA", "VOMITO", "DOR_ABD", "FADIGA", "PERD_OLFT", "PERD_PALA",
    "CARDIOPATI", "HEMATOLOGI", "SIND_DOWN", "HEPATICA", "ASMA", "DIABETES",
    "NEUROLOGIC", "PNEUMOPATI", "IMUNODEPRE", "RENAL", "OBESIDADE", "OBES_IMC", "TABAG",
    "VACINA_COV", "DOSE_1_COV", "DOSE_2_COV", "DOSE_REF", "DOSE_2REF", "DOSE_ADIC",
    "VACINA", "DT_UT_DOSE",
    "CLASSI_FIN", "EVOLUCAO", "DT_EVOLUCA", "DT_ENCERRA", "UTI", "DT_ENTUTI", "DT_SAIDUTI",
]

COLUNAS_DATA = [
    "DT_NOTIFIC", "DT_SIN_PRI", "DT_INTERNA", "DT_EVOLUCA", "DT_ENCERRA",
    "DT_ENTUTI", "DT_SAIDUTI", "DT_UT_DOSE",
    "DOSE_1_COV", "DOSE_2_COV", "DOSE_REF", "DOSE_2REF", "DOSE_ADIC",
]

COLUNAS_TEXTO = ["NU_NOTIFIC", "CS_SEXO", "SG_UF"]

TAMANHO_BLOCO = 50_000


def converter_data(serie):
    s = serie.astype(str)
    iso = s.str.contains("T", na=False)
    barra = ~iso & s.str.contains("/", na=False)
    datas = pd.concat([
        pd.to_datetime(s[iso], format="%Y-%m-%dT%H:%M:%S.%fZ", errors="coerce"),
        pd.to_datetime(s[barra], format="%d/%m/%Y", errors="coerce"),
    ]).reindex(s.index)
    ano = datas.dt.year
    datas = datas.where((ano >= 2015) & (ano <= 2030))
    return pd.to_datetime(datas, errors="coerce")


def idade_em_anos(idade, tipo):
    divisor = tipo.map({1: 365, 2: 12, 3: 1})
    return idade / divisor


def processar(caminho_csv, pasta_saida):
    cabecalho = pd.read_csv(caminho_csv, sep=";", encoding="latin1", nrows=0)
    colunas = [c for c in COLUNAS if c in cabecalho.columns]

    blocos = []
    total = 0
    leitor = pd.read_csv(
        caminho_csv, sep=";", encoding="latin1",
        usecols=colunas, dtype=str, chunksize=TAMANHO_BLOCO,
    )
    for bloco in leitor:
        total += len(bloco)
        covid = bloco[bloco["CLASSI_FIN"].isin(["5", "5.0"])]
        if not covid.empty:
            blocos.append(covid)

    if not blocos:
        print(f"{caminho_csv.name}: nenhum caso de SRAG-COVID ({total} linhas)")
        return None

    base = pd.concat(blocos, ignore_index=True).reindex(columns=COLUNAS)

    for c in COLUNAS:
        if c in COLUNAS_DATA:
            base[c] = converter_data(base[c])
        elif c not in COLUNAS_TEXTO:
            base[c] = pd.to_numeric(base[c], errors="coerce")

    base["IDADE_ANOS"] = idade_em_anos(base["NU_IDADE_N"], base["TP_IDADE"])
    base["arquivo_origem"] = caminho_csv.stem

    base.to_csv(pasta_saida / f"base_covid_{caminho_csv.stem}.csv", index=False)
    print(f"OK: {caminho_csv.name} -> {len(base)} casos de SRAG-COVID ({total} linhas)")
    return base


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pasta")
    parser.add_argument("--saida", default=None)
    args = parser.parse_args()

    entrada = Path(args.pasta)
    if not entrada.is_dir():
        sys.exit(f"Pasta inválida: {entrada}")

    saida = Path(args.saida) if args.saida else entrada / "base_covid"
    saida.mkdir(parents=True, exist_ok=True)

    arquivos = sorted(entrada.glob("*.csv"))
    if not arquivos:
        sys.exit(f"Nenhum .csv encontrado em {entrada}")

    partes = []
    log = saida / "erros_log.txt"
    for arquivo in arquivos:
        try:
            resultado = processar(arquivo, saida)
            if resultado is not None:
                partes.append(resultado)
        except Exception as e:
            print(f"ERRO em {arquivo.name}: {e}")
            with open(log, "a", encoding="utf-8") as f:
                f.write(f"\n=== {arquivo.name} ===\n{traceback.format_exc()}\n")

    if partes:
        combinado = pd.concat(partes, ignore_index=True)
        combinado.to_csv(saida / "base_covid_TODOS.csv", index=False)
        print(f"Base combinada: {len(combinado)} casos em {saida / 'base_covid_TODOS.csv'}")


if __name__ == "__main__":
    main()
