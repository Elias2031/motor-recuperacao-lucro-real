import os

def gerar_relatorios_mensais(dados_por_periodo_e_cnpj):
    """
    Gera, para cada período/CNPJ, um TXT consolidando:
      - bases de débito PIS/COFINS
      - créditos do mês (insumos, devoluções, CT-e)
      - saldo credor anterior e crédito acumulado
      - resumo de ICMS-ST retirado da base
      - detalhamento por CST/alíquota (mesmo raciocínio do M100/M500)
    """
    os.makedirs('RELATORIOS_1', exist_ok=True)

    for periodo, dados_empresa in sorted(dados_por_periodo_e_cnpj.items()):
        nome_arquivo = f"RELATORIOS_1/relatorio_pis_cofins_sped_{periodo}.txt"

        with open(nome_arquivo, 'w', encoding='utf-8') as arq:
            
            razao = dados_empresa.get('razao_social', '')
            cnpj = dados_empresa['emitente']['cnpj']
            # Cabeçalho
            arq.write(f"{'RELATÓRIO PIS/COFINS x SPED':^80}\n")
            arq.write("=" * 80 + "\n")
            arq.write(f"Período: {periodo}\n")
            arq.write(f"CNPJ   : {cnpj}\n")
            arq.write(f"Razão Social: {razao}\n")
            arq.write("=" * 80 + "\n\n")

            # 1) Resumo operacional
            arq.write("1) RESUMO GERAL DAS NOTAS PROCESSADAS\n")
            arq.write("-" * 80 + "\n")
            arq.write(f"   - Total de Notas de Entrada                  : {dados_empresa['num_notas_entrada']}\n")
            arq.write(f"   - Total de Notas CTE                         : {dados_empresa['num_notas_entrada_cte']}\n")
            arq.write(f"   - Total de Notas de Saída                    : {dados_empresa['num_notas_saida']}\n")
            arq.write(f"   - Total de Notas Processadas                 : {dados_empresa['num_notas_entrada'] + dados_empresa['num_notas_saida'] + dados_empresa['num_notas_entrada_cte']}\n")
            arq.write(f"   - Total de Itens Processados                 : {dados_empresa['num_itens_processados']}\n")
            arq.write(f"   - Valor Total das Notas (Saída)              : {dados_empresa['valor_total_nfe']:,.2f}\n")
            arq.write(f"   - Valor Total por Entradas                   : {dados_empresa['valor_total_nfe_entrada']:,.2f}\n")
            arq.write(f"   - Valor Total por Devoluções                 : {dados_empresa['valor_de_devolucao']:,.2f}\n")
            arq.write("\n" + "-" * 80 + "\n\n")

            # 2) Bases principais PIS/COFINS
            arq.write("2) BASES DE CÁLCULO PIS/COFINS (APURAÇÃO / SPED)\n")
            arq.write("-" * 80 + "\n")

            base_original = float(dados_empresa.get('base_original_pis_cofins', 0) or 0)
            credito_icms_st = float(dados_empresa.get('credito_pis_cofins_icms_st', 0) or 0)
            base_sem_icms_st = float(dados_empresa.get('base_pis_cofins_sem_icms_st', 0) or 0)
            base_pis_cofins_com_icms_proprio = float(dados_empresa.get('base_pis_cofins_com_icms_proprio', 0) or 0)

            debito_pis_mes = float(dados_empresa.get('debito_pis_do_mes', 0) or 0)
            debito_cofins_mes = float(dados_empresa.get('debito_cofins_do_mes', 0) or 0)
            debito_icms_retirado_pis_cofins = float(dados_empresa.get('debito_icms_retirar_base_pis_cofins', 0) or 0)
            
            
            arq.write(f"   - Base original PIS/COFINS                   : {base_pis_cofins_com_icms_proprio:,.2f}\n")
            arq.write(f"   - ICMS próprio retirado da base de PIS/COFINS: {debito_icms_retirado_pis_cofins:,.2f}\n")
            arq.write(f"   - Base PIS/COFINS sem ICMS                   : {base_original:,.2f}\n")
            arq.write(f"   - ICMS-ST excluído da base (Solução COSIT)   : {credito_icms_st:,.2f}\n")
            arq.write(f"   - Base ajustada PIS/COFINS (sem ICMS-ST)     : {base_sem_icms_st:,.2f}\n")
            arq.write("\n")
            arq.write(f"   - Débito PIS (1,65% sobre base ajustada)     : {debito_pis_mes:,.2f}\n")
            arq.write(f"   - Débito COFINS (7,60% sobre base ajustada)  : {debito_cofins_mes:,.2f}\n")
            arq.write(f"   - Débito TOTAL PIS + COFINS                  : {(debito_pis_mes + debito_cofins_mes):,.2f}\n")
            arq.write("\n")

            # 3) Créditos do mês
            arq.write("3) CRÉDITOS DO MÊS PIS/COFINS (ENTRADAS)\n")
            arq.write("-" * 80 + "\n")

            cred_insumos = float(dados_empresa.get('credito_por_entradas_pis_cofins', 0) or 0)
            cred_devol = float(dados_empresa.get('credito_por_entradas_pis_cofins_devolucao', 0) or 0)
            cred_cte_base = float(dados_empresa.get('credito_por_entradas_cte_pis_cofins', 0) or 0)

            cred_pis_mes = float(dados_empresa.get('credito_pis_do_mes', 0) or 0)
            cred_cofins_mes = float(dados_empresa.get('credito_cofins_do_mes', 0) or 0)

            # NOVO: bases por natureza, calculadas lá na apuração (M105 usa a mesma lógica)
            bases_nat = dados_empresa.get('base_credito_nat_pis_cofins', {}) or {}

            base_revenda    = float(bases_nat.get('01', 0) or 0)
            base_insumos    = float(bases_nat.get('02', 0) or 0)
            base_servicos   = float(bases_nat.get('03', 0) or 0)
            base_devolucao  = float(bases_nat.get('12', 0) or 0)
            base_sem_credito = float(bases_nat.get('13', 0) or 0)
            # Se você quiser mostrar transporte dentro de insumos, ignore aqui;
            # CT-e já está separado em cred_cte_base.

            arq.write(f"   - Base de crédito por insumos/bens (total) : {cred_insumos:,.2f}\n")
            arq.write(f"       • Revenda (cod. nat 01)                : {base_revenda:,.2f}\n")
            arq.write(f"       • Insumos/uso/consumo (cod. nat 02)    : {base_insumos:,.2f}\n")
            arq.write(f"       • Serviços tomados (cod. nat 03)       : {base_servicos:,.2f}\n")
            arq.write(f"       • Devoluções (cod. nat 12)             : {base_devolucao:,.2f}\n")
            arq.write(f"       • Base sem direito a crédito (cod. 13) : {base_sem_credito:,.2f}\n")
            arq.write(f"\n")
            arq.write(f"   - Base de crédito por devoluções           : {cred_devol:,.2f}\n")
            arq.write(f"   - Base de crédito por CT-e (fretes)        : {cred_cte_base:,.2f}\n")
            arq.write(f"   - Base total de crédito PIS/COFINS         : {float(dados_empresa.get('base_credito_total_pis_cofins', 0) or 0):,.2f}\n")
            arq.write("\n")
            arq.write(f"   - Crédito PIS do mês (apuração)            : {cred_pis_mes:,.2f}\n")
            arq.write(f"   - Crédito COFINS do mês (apuração)         : {cred_cofins_mes:,.2f}\n")
            arq.write(f"   - Crédito TOTAL PIS + COFINS no mês        : {(cred_pis_mes + cred_cofins_mes):,.2f}\n")
            arq.write("\n")

            # 4) Saldos credores e débito a pagar
            arq.write("4) SALDOS CREDORES E DÉBITO A PAGAR\n")
            arq.write("-" * 80 + "\n")

            saldo_ant_pis = float(dados_empresa.get('saldo_credor_anterior_pis', 0) or 0)
            saldo_ant_cofins = float(dados_empresa.get('saldo_credor_anterior_cofins', 0) or 0)

            debito_pis_pagar = float(dados_empresa.get('debito_a_pagar_pis', 0) or 0)
            debito_cofins_pagar = float(dados_empresa.get('debito_a_pagar_cofins', 0) or 0)
            debito_total_pagar = float(dados_empresa.get('debito_a_pagar_total', debito_pis_pagar + debito_cofins_pagar) or 0)

            cred_acum_pis = float(dados_empresa.get('credito_acumulado_pis', 0) or 0)
            cred_acum_cofins = float(dados_empresa.get('credito_acumulado_cofins', 0) or 0)

            arq.write(f"   - Saldo credor anterior PIS                  : {saldo_ant_pis:,.2f}\n")
            arq.write(f"   - Saldo credor anterior COFINS               : {saldo_ant_cofins:,.2f}\n")
            arq.write("\n")
            arq.write(f"   - Débito a pagar PIS                         : {debito_pis_pagar:,.2f}\n")
            arq.write(f"   - Débito a pagar COFINS                      : {debito_cofins_pagar:,.2f}\n")
            arq.write(f"   - Débito a pagar TOTAL                       : {debito_total_pagar:,.2f}\n")
            arq.write("\n")
            arq.write(f"   - Crédito acumulado PIS após compensações    : {cred_acum_pis:,.2f}\n")
            arq.write(f"   - Crédito acumulado COFINS após compensações : {cred_acum_cofins:,.2f}\n")
            arq.write("\n")

            # 5) Detalhamento por CST/alíquota (PIS)
            arq.write("5) DETALHAMENTO DOS CRÉDITOS POR CST/ALÍQUOTA - PIS (base do M100/M105)\n")
            arq.write("-" * 80 + "\n")

            base_pis_por_chave = dados_empresa.get('base_credito_pis_no_mes', {}) or {}
            cred_pis_por_chave = dados_empresa.get('credito_pis_por_chave_no_mes', {}) or {}

            if base_pis_por_chave:
                # cabeçalho mais compacto
                arq.write(f"{'CST':<4} {'Aliq%':>6} {'Base Créd.':>14} {'Créd. Orig.':>14} {'Créd. Final':>14} {'Abat. Acum.':>14}\n")
                arq.write("-" * 80 + "\n")
                for chave in sorted(base_pis_por_chave.keys()):
                    info = cred_pis_por_chave.get(chave, {})
                    cst = info.get('cst', chave.split('_')[0])
                    aliq = info.get('aliquota', chave.split('_')[1])
                    base_cred = float(base_pis_por_chave.get(chave, 0) or 0)
                    cred_orig = float(info.get('credito_original', 0) or 0)
                    cred_desc = float(info.get('credito_descontado', 0) or 0)
                    abatido = float(info.get('valor_abatido', 0) or 0)

                    arq.write(
                        f"{cst:<4} {aliq:>6} {base_cred:>14,.2f} {cred_orig:>14,.2f} {cred_desc:>14,.2f} {abatido:>14,.2f}\n"
                    )
            else:
                arq.write("   Nenhum crédito de PIS calculado no mês.\n")
            # apenas uma quebra de linha ao final do bloco
            arq.write("\n")
            arq.write("\n")

            # 6) Detalhamento por CST/alíquota (COFINS)
            arq.write("6) DETALHAMENTO DOS CRÉDITOS POR CST/ALÍQUOTA - COFINS (base do M500/M505)\n")
            arq.write("-" * 80 + "\n")

            base_cofins_por_chave = dados_empresa.get('base_credito_cofins_no_mes', {}) or {}
            cred_cofins_por_chave = dados_empresa.get('credito_cofins_por_chave_no_mes', {}) or {}

            if base_cofins_por_chave:
                # cabeçalho mais compacto
                arq.write(f"{'CST':<4} {'Aliq%':>6} {'Base Créd.':>14} {'Créd. Orig.':>14} {'Créd. Final':>14} {'Abat. Acum.':>14}\n")
                arq.write("-" * 80 + "\n")
                for chave in sorted(base_cofins_por_chave.keys()):
                    info = cred_cofins_por_chave.get(chave, {})
                    cst = info.get('cst', chave.split('_')[0])
                    aliq = info.get('aliquota', chave.split('_')[1])
                    base_cred = float(base_cofins_por_chave.get(chave, 0) or 0)
                    cred_orig = float(info.get('credito_original', 0) or 0)
                    cred_desc = float(info.get('credito_descontado', 0) or 0)
                    abatido = float(info.get('valor_abatido', 0) or 0)

                    arq.write(
                        f"{cst:<4} {aliq:>6} {base_cred:>14,.2f} {cred_orig:>14,.2f} {cred_desc:>14,.2f} {abatido:>14,.2f}\n"
                    )
            else:
                arq.write("   Nenhum crédito de COFINS calculado no mês.\n")
            arq.write("\n")

            # 7) Resumo CT-e
            arq.write("7) Apuração de ICMS :\n")
            arq.write(f"   - Saldo credor anterior                      : {round(dados_empresa['saldo_credor_anterior'], 2):,.2f}\n")
            arq.write(f"   - Base de calculo ICMS                       : {round(dados_empresa['base_icms'], 2):,.2f}\n\n")
            arq.write(f"   - cREDITO AJUSTE ITENS ERRADOS               : {round(dados_empresa['valor_a_recuperar_icms'], 2):,.2f}\n\n")
            
            arq.write(f"   - Crédito por entradas ICMS                  : {round(dados_empresa['credito_por_entradas_icms'], 2):,.2f}\n")
            arq.write(f"   - Crédito por CTE ICMS                       : {round(dados_empresa['credito_por_entradas_cte_icms'], 2):,.2f}\n")
            arq.write(f"   - Crédito total ICMS                         : {round(dados_empresa['credito_total_icms'], 2):,.2f}\n\n")
            
            arq.write(f"   - Débito por saidas ICMS                     : {round(dados_empresa['debito_icms'], 2):,.2f}\n")
            arq.write(f"   - Débito a pagar ICMS                        : {round(dados_empresa['debito_a_pagar_icms'], 2):,.2f}\n\n")
                
            arq.write(f"   - Saldo Credor a transportar                 : {round(dados_empresa['saldo_credor_a_transportar'], 2):,.2f}\n\n")
            arq.write(f"   - Credito Acumulado ICMS                     : {round(dados_empresa['credito_acumulado_icms'], 2):,.2f}\n")

            arq.write("=" * 80 + "\n")
            arq.write("Fim do relatório.\n")
