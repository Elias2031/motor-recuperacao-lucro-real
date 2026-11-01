from MODULES.speds.processar_sped_contribuicoes import determinar_cod_nat_base_credito
from MODULES.utilitarios import normaliza_aliquota
from collections import defaultdict
import pandas as pd
from pathlib import Path


CSTS_CREDITO = {'50','51','52','53','54','55','56','60','61','62','63','64','65','66'}
MAP_CST_GRUPOS = {
    '50': (100,), '51': (200,), '52': (300,),
    '53': (100, 200), '54': (100, 300), '55': (200, 300),
    '56': (100, 200, 300),
    '60': (100,), '61': (200,), '62': (300,),
    '63': (100, 200), '64': (100, 300), '65': (200, 300),
    '66': (100, 200, 300),
}

def gerar_relatorio_apuracao_pis_cofins(dados_por_periodo_e_cnpj, caminho_saida="relatorios_apuracao"):
    Path(caminho_saida).mkdir(exist_ok=True)

    for periodo in dados_por_periodo_e_cnpj:
        dados = dados_por_periodo_e_cnpj[periodo]
        linhas = []
        linhas.append(f"RELATÓRIO DE APURAÇÃO – PIS/COFINS\n")
        # linhas.append(f"Período: {periodo}\nCNPJ: {cnpj}\n")
        linhas.append("="*70 + "\n")

        # --- BASES DE CÁLCULO ---
        linhas.append("BASES DE CÁLCULO:\n")
        linhas.append(f"  Base Original: {dados.get('base_original_pis_cofins', 0):,.2f}\n")
        linhas.append(f"  Base sem ICMS-ST: {dados.get('base_pis_cofins_sem_icms_st', 0):,.2f}\n")
        linhas.append(f"  Base com ICMS Próprio: {dados.get('base_pis_cofins_com_icms_proprio', 0):,.2f}\n\n")

        base_nat = dados.get("base_credito_nat_pis_cofins", {})
        if base_nat:
            linhas.append("  Base de Crédito por Natureza:\n")
            for cod_nat, valor in base_nat.items():
                linhas.append(f"    {cod_nat}: {valor:,.2f}\n")
            linhas.append("\n")

        # --- DÉBITOS ---
        linhas.append("DÉBITOS:\n")
        linhas.append(f"  PIS: Base={dados.get('base_pis_cofins_sem_icms_st',0):,.2f} → {dados.get('debito_pis_do_mes',0):,.2f}\n")
        linhas.append(f"  COFINS: Base={dados.get('base_pis_cofins_sem_icms_st',0):,.2f} → {dados.get('debito_cofins_do_mes',0):,.2f}\n\n")

        # --- CRÉDITOS ---
        linhas.append("CRÉDITOS PIS:\n")
        for chave, info in dados.get("credito_pis_por_chave_no_mes", {}).items():
            linhas.append(f"  {chave}: base={info['base_calculo']:,.2f}, aliq={info['aliquota']}%, crédito={info['credito_original']:,.2f}, descontado={info['credito_descontado']:,.2f}, abatido={info['valor_abatido']:,.2f}\n")
        linhas.append("\nCRÉDITOS COFINS:\n")
        for chave, info in dados.get("credito_cofins_por_chave_no_mes", {}).items():
            linhas.append(f"  {chave}: base={info['base_calculo']:,.2f}, aliq={info['aliquota']}%, crédito={info['credito_original']:,.2f}, descontado={info['credito_descontado']:,.2f}, abatido={info['valor_abatido']:,.2f}\n")

        # --- SALDOS E ABATIMENTOS ---
        linhas.append("\nSALDOS E ABATIMENTOS:\n")
        linhas.append(f"  Saldo Credor Anterior PIS: {dados.get('saldo_credor_anterior_pis', 0):,.2f}\n")
        linhas.append(f"  Saldo Credor Anterior COFINS: {dados.get('saldo_credor_anterior_cofins', 0):,.2f}\n")
        linhas.append(f"  Crédito do Mês PIS: {dados.get('credito_pis_do_mes', 0):,.2f}\n")
        linhas.append(f"  Crédito do Mês COFINS: {dados.get('credito_cofins_do_mes', 0):,.2f}\n")
        linhas.append(f"  Crédito Acumulado Final PIS: {dados.get('credito_acumulado_pis', 0):,.2f}\n")
        linhas.append(f"  Crédito Acumulado Final COFINS: {dados.get('credito_acumulado_cofins', 0):,.2f}\n")
        linhas.append(f"  Débito a Pagar PIS: {dados.get('debito_a_pagar_pis', 0):,.2f}\n")
        linhas.append(f"  Débito a Pagar COFINS: {dados.get('debito_a_pagar_cofins', 0):,.2f}\n")
        linhas.append(f"  TOTAL A PAGAR: {dados.get('debito_a_pagar_total', 0):,.2f}\n")
        linhas.append("="*70 + "\n")

        # --- SALVA ---
        caminho_arquivo = Path(caminho_saida) / f"{periodo}.txt"
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.writelines(linhas)

def codigo_credito_por_aliquota(cst: str, aliquota: float) -> list:
    """
    Retorna uma lista de códigos de crédito (101–308) com base no CST e na alíquota PIS/COFINS.
    Regra:
      - alíquota == 0.65 ou 1.65 → código básico (x01, x02, x03)
      - alíquota == 0 ou qualquer outra → alíquota diferenciada (x02, x202, x302)
    """
    cst = str(cst).zfill(2)
    grupos = MAP_CST_GRUPOS.get(cst, ())
    codigos = []

    for grupo in grupos:
        if str(aliquota) in ('0.65', '1.65', '7.60', '3.00'):
            cod_base = str(grupo + 1)  # 100→101, 200→201, 300→301
        else:
            cod_base = str(grupo + 2)  # 100→102, 200→202, 300→302
        codigos.append(cod_base)

    return codigos

def calcular_credito_mes_pis_cofins(dados_cnpj):
    acumulador_cst_pis = defaultdict(float)
    base_credito_pis = defaultdict(float)
    combos_cst_aliq_pis = set()
    
    acumulador_cst_cofins = defaultdict(float)
    base_credito_cofins = defaultdict(float)
    combos_cst_aliq_cofins = set()

    # NOVO: base por natureza (revenda, insumo, etc.) – só insumos/bens, sem CT-e
    base_credito_nat = defaultdict(float)  # chave = '01','02','03','12','13','14'

    for nota in dados_cnpj['notas']:
        if nota['indicador_operacao'] == '0':  # entradas
            for item in nota['itens']:
                # --- PIS ---
                cst_pis = str(item.get('cst_pis', '')).zfill(2)
                aliquota_pis = float(item.get('aliq_pis', 0.0))
                aliquota_pis = normaliza_aliquota(aliquota_pis)

                try:
                    valor_pago_pis = float(item.get('valor_pis', 0.0))
                except ValueError:
                    valor_pago_pis = 0.0
                try:
                    base_pis = float(item.get('base_calculo_pis', 0.0))
                except ValueError:
                    base_pis = 0.0
                    
                codigos = codigo_credito_por_aliquota(cst_pis, aliquota_pis)
                if not codigos:
                    # print(f'AVISO: CST {cst} não mapeado para códigos de crédito. Pulando...')
                    continue
                

                cod_nat = determinar_cod_nat_base_credito(item)
                
                if cod_nat:
                    chave_pis = f'{cst_pis}_{aliquota_pis}'
                    acumulador_cst_pis[chave_pis] += valor_pago_pis
                    base_credito_pis[chave_pis] += base_pis
                    combos_cst_aliq_pis.add((cst_pis, aliquota_pis))

                    base_credito_nat[cod_nat] += base_pis

                # --- COFINS ---
                cst_cofins = str(item.get('cst_cofins', '')).zfill(2)
                aliquota_cofins = float(item.get('aliq_cofins', 0.0))
                aliquota_cofins = normaliza_aliquota(aliquota_cofins)

                try:
                    valor_pago_cofins = float(item.get('valor_cofins', 0.0))
                except ValueError:
                    valor_pago_cofins = 0.0
                try:
                    base_cofins = float(item.get('base_calculo_cofins', 0.0))
                except ValueError:
                    base_cofins = 0.0

                if cod_nat:
                    chave_cofins = f'{cst_cofins}_{aliquota_cofins}'
                    acumulador_cst_cofins[chave_cofins] += valor_pago_cofins
                    base_credito_cofins[chave_cofins] += base_cofins
                    combos_cst_aliq_cofins.add((cst_cofins, aliquota_cofins))
                    
    # === PIS ===
    credito_mes_pis = 0.0
    credito_pis_por_chave = {}

    for cst, aliquota_calculo in combos_cst_aliq_pis:
        aliquota_norm = normaliza_aliquota(aliquota_calculo)
        chave = f'{cst}_{aliquota_norm}'

        # CT-e soma só na base de frete, NÃO nas bases de insumos/bens
        if cst == '50' and aliquota_norm == '1.65':
            base_credito_pis[chave] += float(dados_cnpj.get('credito_por_entradas_cte_pis_cofins', 0.0))

        percentual = float(str(aliquota_calculo).replace(',', '.'))
        base_chave = base_credito_pis[chave]
        credito_chave = base_chave * (percentual / 100.0)

        credito_pis_por_chave[chave] = {
            'cst': cst,
            'aliquota': aliquota_norm,
            'base_calculo': base_chave,
            'percentual': percentual,
            'credito_original': credito_chave,
            'credito_descontado': credito_chave,
            'valor_abatido': 0.0
        }

        credito_mes_pis += credito_chave

    # === COFINS ===
    credito_mes_cofins = 0.0
    credito_cofins_por_chave = {}

    for cst, aliquota_calculo in combos_cst_aliq_cofins:
        aliquota_norm = normaliza_aliquota(aliquota_calculo)
        chave = f'{cst}_{aliquota_norm}'

        if cst == '50' and aliquota_norm == '7.60':
            base_credito_cofins[chave] += float(dados_cnpj.get('credito_por_entradas_cte_pis_cofins', 0.0))

        percentual = float(str(aliquota_calculo).replace(',', '.'))
        base_chave = base_credito_cofins[chave]
        credito_chave = base_chave * (percentual / 100.0)

        credito_cofins_por_chave[chave] = {
            'cst': cst,
            'aliquota': aliquota_norm,
            'base_calculo': base_chave,
            'percentual': percentual,
            'credito_original': credito_chave,
            'credito_descontado': credito_chave,
            'valor_abatido': 0.0
        }

        credito_mes_cofins += credito_chave

    # Guarda também a base por natureza dentro do próprio dados_cnpj,
    # se você quiser reaproveitar em outras funções (M105, relatórios, etc.)
    dados_cnpj['base_credito_nat_pis_cofins'] = dict(base_credito_nat)

    return {
        "credito_mes_pis": credito_mes_pis,
        "credito_mes_cofins": credito_mes_cofins,
        "base_credito_pis": dict(base_credito_pis),
        "base_credito_cofins": dict(base_credito_cofins),
        "credito_pis_por_chave": credito_pis_por_chave,
        "credito_cofins_por_chave": credito_cofins_por_chave,
        "base_credito_nat_pis_cofins": dict(base_credito_nat),  # <<< NOVO
    }

def apurar_pis_cofins(dados_por_periodo_e_cnpj):
    credito_acumulado_pis = 0
    credito_acumulado_cofins = 0

    for periodo in sorted(dados_por_periodo_e_cnpj.keys()):
            
            base_original_pis_cofins = 0
            base_pis_cofins_sem_icms_st = 0
            dados_empresa = dados_por_periodo_e_cnpj[periodo]

            dados_empresa['saldo_credor_anterior_pis'] = credito_acumulado_pis
            dados_empresa['saldo_credor_anterior_cofins'] = credito_acumulado_cofins
            
            dados_credito_mes = calcular_credito_mes_pis_cofins(dados_empresa)
            
            credito_pis_do_mes = dados_credito_mes['credito_mes_pis']
            credito_cofins_do_mes = dados_credito_mes['credito_mes_cofins']
            
            base_credito_pis = dados_credito_mes['base_credito_pis']
            base_credito_cofins = dados_credito_mes['base_credito_cofins']
            
            credito_pis_por_chave = dados_credito_mes['credito_pis_por_chave']
            credito_cofins_por_chave = dados_credito_mes['credito_cofins_por_chave']
            
            base_pis_cofins_com_icms_proprio = sum(
                round(float(item['valor']), 2)
                for nota in dados_empresa['notas']
                for item in nota['itens']
                if nota['indicador_operacao'] == '1'  # apenas saídas
                and item['cst_pis_correto'] == '01'
                and float(item['aliquota_pis_correto']) > 0
            )
            dados_empresa['base_pis_cofins_com_icms_proprio'] = base_pis_cofins_com_icms_proprio

            base_original_pis_cofins = sum(
                round(float(item['base_calculo_pis_correto']), 2)
                for nota in dados_empresa['notas']
                for item in nota['itens']
                if nota['indicador_operacao'] == '1'  # apenas saídas
                and item['cst_pis_correto'] == '01'
                and float(item['aliquota_pis_correto']) > 0
            )
            dados_empresa['base_original_pis_cofins'] = base_original_pis_cofins

            base_pis_cofins_sem_icms_st = (
                base_original_pis_cofins
                - float(dados_empresa['credito_pis_cofins_icms_st'])
            )
            dados_empresa['base_pis_cofins_sem_icms_st'] = base_pis_cofins_sem_icms_st

            debito_pis_do_mes = base_pis_cofins_sem_icms_st * 0.0165
            debito_cofins_do_mes = base_pis_cofins_sem_icms_st * 0.076

            debito_a_pagar_pis = debito_pis_do_mes - credito_pis_do_mes
            debito_a_pagar_cofins = debito_cofins_do_mes - credito_cofins_do_mes

            if debito_a_pagar_pis <= 0:
                credito_acumulado_pis += -debito_a_pagar_pis
                debito_a_pagar_pis = 0
            elif debito_a_pagar_pis > 0:
                if credito_acumulado_pis >= debito_a_pagar_pis:
                    credito_acumulado_pis -= debito_a_pagar_pis
                    debito_a_pagar_pis = 0
                elif credito_acumulado_pis < debito_a_pagar_pis:
                    debito_a_pagar_pis -= credito_acumulado_pis
                    credito_acumulado_pis = 0

            if debito_a_pagar_cofins <= 0:
                credito_acumulado_cofins += -debito_a_pagar_cofins
                debito_a_pagar_cofins = 0
            elif debito_a_pagar_cofins > 0:
                if credito_acumulado_cofins >= debito_a_pagar_cofins:
                    credito_acumulado_cofins -= debito_a_pagar_cofins
                    debito_a_pagar_cofins = 0
                else:
                    debito_a_pagar_cofins -= credito_acumulado_cofins
                    credito_acumulado_cofins = 0
            
            if credito_acumulado_pis > 0 and credito_pis_por_chave:
                # pega a chave com MAIOR crédito (pode usar original ou descontado; aqui uso o descontado)
                chave_maior_credito_pis = max(
                    credito_pis_por_chave,
                    key=lambda k: credito_pis_por_chave[k]['credito_original']
                )
                
                maior_credito_pis = credito_pis_por_chave[chave_maior_credito_pis]['credito_original']
                
                if maior_credito_pis > credito_acumulado_pis:
                    credito_descontado = maior_credito_pis - credito_acumulado_pis

                    credito_pis_por_chave[chave_maior_credito_pis]['credito_descontado'] = credito_descontado
                    credito_pis_por_chave[chave_maior_credito_pis]['valor_abatido'] += credito_acumulado_pis
                else:
                    print('AVISO: crédito acumulado PIS maior que o maior crédito por chave!', periodo)

            # --- COFINS ---
            if credito_acumulado_cofins > 0 and credito_cofins_por_chave:
                chave_maior_credito_cofins = max(
                    credito_cofins_por_chave,
                    key=lambda k: credito_cofins_por_chave[k]['credito_original']
                )

                maior_credito_cofins = credito_cofins_por_chave[chave_maior_credito_cofins]['credito_original']

                if maior_credito_cofins > credito_acumulado_cofins:
                    credito_descontado = maior_credito_cofins - credito_acumulado_cofins

                    credito_cofins_por_chave[chave_maior_credito_cofins]['credito_descontado'] = credito_descontado
                    credito_cofins_por_chave[chave_maior_credito_cofins]['valor_abatido'] += credito_acumulado_cofins
                else:
                    print('AVISO: crédito acumulado COFINS maior que o maior crédito por chave!', periodo)
            
            desconto_total_pis = sum(
                (v.get('credito_descontado', 0.0))
                for v in (credito_pis_por_chave or {}).values()
            )
            desconto_total_cofins = sum(
                (v.get('credito_descontado', 0.0))
                for v in (credito_cofins_por_chave or {}).values()
            )
            credito_descontado_total = float(desconto_total_pis) + float(desconto_total_cofins)
            
            dados_empresa['base_credito_pis_no_mes'] = base_credito_pis
            dados_empresa['base_credito_cofins_no_mes'] = base_credito_cofins
            dados_empresa['credito_pis_do_mes'] = credito_pis_do_mes
            dados_empresa['credito_cofins_do_mes'] = credito_cofins_do_mes
            dados_empresa['credito_pis_por_chave_no_mes'] = credito_pis_por_chave
            dados_empresa['credito_cofins_por_chave_no_mes'] = credito_cofins_por_chave
            dados_empresa['credito_acumulado_pis'] = credito_acumulado_pis
            dados_empresa['credito_acumulado_cofins'] = credito_acumulado_cofins
            dados_empresa['debito_pis_do_mes'] = debito_pis_do_mes
            dados_empresa['debito_cofins_do_mes'] = debito_cofins_do_mes
            dados_empresa['debito_a_pagar_pis'] = debito_a_pagar_pis
            dados_empresa['debito_a_pagar_cofins'] = debito_a_pagar_cofins
            dados_empresa['debito_a_pagar_total'] = (debito_a_pagar_pis + debito_a_pagar_cofins)
            dados_empresa['base_credito_nat_pis_cofins'] = dados_credito_mes['base_credito_nat_pis_cofins']
            dados_empresa['credito_descontado_total_pis'] = desconto_total_pis
            dados_empresa['credito_descontado_total_cofins'] = desconto_total_cofins
            dados_empresa['credito_descontado_total'] = credito_descontado_total

