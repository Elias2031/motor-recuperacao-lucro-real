import pandas as pd
import re
from decimal import Decimal

def gerar_planilha_apuracao_consolidada(dados_por_periodo_e_cnpj):
    def normalizar_num(valor):
        """Converte str, float, Decimal, bytes ou None em float seguro."""
        if valor is None:
            return 0.0
        if isinstance(valor, (int, float)):
            return round(float(valor), 2)
        if isinstance(valor, Decimal):
            return round(float(valor), 2)
        if isinstance(valor, bytes):
            try:
                valor = valor.decode('utf-8', errors='ignore')
            except Exception:
                return 0.0
        if isinstance(valor, str):
            # remove caracteres não numéricos
            valor = valor.strip().replace(',', '.')
            valor = re.sub(r'[^0-9\.-]', '', valor)
        try:
            return round(float(valor), 2)
        except Exception:
            return 0.0

    linhas = []
    for periodo, dados in sorted(dados_por_periodo_e_cnpj.items()):
            linha = {
                'Periodo': periodo,
                # 'CNPJ': dados['emitente']['cnpj'],
                # 'Debito a Pagar PIS': normalizar_num(dados.get('debito_a_pagar_pis')),
                # 'Debito a Pagar COFINS': normalizar_num(dados.get('debito_a_pagar_cofins')),
                # 'Credito PIS no Mes': normalizar_num(dados.get('credito_pis_do_mes')),
                # 'Credito COFINS no Mes': normalizar_num(dados.get('credito_cofins_do_mes')),
                # 'Credito Acumulado PIS': normalizar_num(dados.get('credito_acumulado_pis')),
                # 'Credito Acumulado COFINS': normalizar_num(dados.get('credito_acumulado_cofins')),
                # 'DEBITO A PAGAR ICMS ORIGINAL': normalizar_num(dados.get('debito_original_icms')),
                'Debito por saidas ICMS APURADO': normalizar_num(dados.get('debito_icms')),
                # 'Credito do mes ICMS APURADO': normalizar_num(dados.get('credito_total_icms')),
                'Debito a pagar ICMS APURADO': normalizar_num(dados.get('debito_a_pagar_icms')),
                'Credito Acumulado ICMS APURADO': normalizar_num(dados.get('credito_acumulado_icms')),
                'Credito ajuste APURADO': normalizar_num(dados.get('soma_valores_a_recuperar_icms')),
            }
            linhas.append(linha)

    df = pd.DataFrame(linhas)
    colunas_numericas = [c for c in df.columns if c not in ('Periodo', 'CNPJ')]
    df[colunas_numericas] = df[colunas_numericas].apply(pd.to_numeric, errors='coerce')

    df.to_excel("apuracao_por_periodo.xlsx", index=False)
    return df
