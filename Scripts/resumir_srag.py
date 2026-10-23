import sys
import argparse
from pathlib import Path
import pandas as pd


def resumir(caminho_csv, pasta_saida):
    df = pd.read_csv(caminho_csv, sep=";", encoding="latin1", low_memory=False)

    datas = pd.to_datetime(df["DT_NOTIFIC"], errors="coerce", utc=True).dt.tz_localize(None)

    bins = [0, 5, 12, 18, 30, 45, 60, 75, 200]
    labels = ["0-4", "5-11", "12-17", "18-29", "30-44", "45-59", "60-74", "75+"]

    novas = pd.DataFrame({
        "mes": datas.dt.to_period("M").astype(str),
        "faixa_etaria": pd.cut(df["NU_IDADE_N"], bins=bins, labels=labels, right=False),
        "caso_covid": df["CLASSI_FIN"] == 5,
        "obito_srag": df["EVOLUCAO"] == 2,
        "foi_uti": df["UTI"] == 1,
        "caso_encerrado": df["DT_ENCERRA"].notna(),
        "vacinado_cov": df["VACINA_COV"] == 1,
    })
    df = pd.concat([df, novas], axis=1)

    mensal = df.groupby("mes").agg(
        total_casos=("NU_NOTIFIC", "count"),
        casos_covid=("caso_covid", "sum"),
        casos_encerrados=("caso_encerrado", "sum"),
        obitos_srag=("obito_srag", "sum"),
        casos_uti=("foi_uti", "sum"),
        casos_vacinados_cov=("vacinado_cov", "sum"),
        vacina_cov_preenchido=("VACINA_COV", lambda s: s.notna().sum()),
        idade_media=("NU_IDADE_N", "mean"),
    ).reset_index()

    faixa = df.groupby(["mes", "faixa_etaria"], observed=True).size().reset_index(name="casos")

    fechados = df[df["caso_covid"] & df["caso_encerrado"]]
    vacinacao = (
        fechados.groupby(["mes", "VACINA_COV", "EVOLUCAO"], observed=True)
        .size()
        .reset_index(name="casos")
    )

    nome = Path(caminho_csv).stem
    for tabela in (mensal, faixa, vacinacao):
        tabela["arquivo_origem"] = nome

    mensal.to_csv(pasta_saida / f"resumo_mensal_{nome}.csv", index=False)
    faixa.to_csv(pasta_saida / f"resumo_faixa_etaria_{nome}.csv", index=False)
    vacinacao.to_csv(pasta_saida / f"resumo_vacinacao_desfecho_{nome}.csv", index=False)

    print(f"OK: {nome} ({len(df)} linhas)")
    return mensal, faixa, vacinacao


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pasta")
    parser.add_argument("--saida", default=None)
    args = parser.parse_args()

    entrada = Path(args.pasta)
    if not entrada.is_dir():
        sys.exit(f"Pasta inválida: {entrada}")

    saida = Path(args.saida) if args.saida else entrada / "resumos"
    saida.mkdir(parents=True, exist_ok=True)

    arquivos = sorted(entrada.glob("*.csv"))
    if not arquivos:
        sys.exit(f"Nenhum .csv encontrado em {entrada}")

    resultados = []
    for arquivo in arquivos:
        try:
            resultados.append(resumir(arquivo, saida))
        except Exception as e:
            print(f"ERRO em {arquivo.name}: {e}")

    if resultados:
        nomes = ["resumo_mensal", "resumo_faixa_etaria", "resumo_vacinacao_desfecho"]
        for i, nome in enumerate(nomes):
            combinado = pd.concat([r[i] for r in resultados], ignore_index=True).sort_values("mes")
            combinado.to_csv(saida / f"{nome}_TODOS.csv", index=False)
        print(f"Resumos combinados salvos em {saida}")


if __name__ == "__main__":
    main()
