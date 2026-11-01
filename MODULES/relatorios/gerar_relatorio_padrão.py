import os 

def gerar_relatorios_mensais_padrao(dados_por_periodo_e_cnpj):  
    
    os.makedirs('RELATORIOS', exist_ok=True)
    
    for periodo in sorted(dados_por_periodo_e_cnpj.keys()):
        for cnpj in dados_por_periodo_e_cnpj[periodo]:
            nome_arquivo = f"RELATORIOS/relatorio_mensal{cnpj}_{periodo}.txt"
            with open(nome_arquivo, 'w', encoding='utf-8') as arquivo_txt:
                dados_empresa = dados_por_periodo_e_cnpj[periodo]
                
                arquivo_txt.write(f"{'RELATÓRIO MENSAL':^80}\n")
                arquivo_txt.write("=" * 80 + "\n")
                
                arquivo_txt.write(f"Período: {periodo}\n")
                arquivo_txt.write(f"CNPJ: {cnpj}\n")
                arquivo_txt.write(f"Razão Social: {dados_empresa['razao_social']}\n")
                
                arquivo_txt.write("=" * 80 + "\n\n")
                arquivo_txt.write(">> RESUMO GERAL DO PERÍODO:\n")
                
                arquivo_txt.write(f"   - Total de Notas de Entrada            : {dados_empresa['num_notas_entrada']}\n")
                arquivo_txt.write(f"   - Total de Notas CTE                   : {dados_empresa['num_notas_entrada_cte']}\n")
                arquivo_txt.write(f"   - Total de Notas de Saída              : {dados_empresa['num_notas_saida']}\n")
                arquivo_txt.write(f"   - Total de Notas Processadas           : {dados_empresa['num_notas_entrada'] + dados_empresa['num_notas_saida'] + dados_empresa['num_notas_entrada_cte']}\n")
                arquivo_txt.write(f"   - Total de Itens Processados           : {dados_empresa['num_itens_processados']}\n")
                arquivo_txt.write(f"   - Valor Total das Notas (Saída)        : {dados_empresa['valor_total_nfe']:,.2f}\n")
                arquivo_txt.write(f"   - Valor Total das Notas (Saída)        : {dados_empresa['valor_total_nfe_minha_base']:,.2f}\n")
                arquivo_txt.write(f"   - Valor Total por Entradas             : {dados_empresa['valor_total_nfe_entrada']:,.2f}\n")
                arquivo_txt.write(f"   - Valor Total por Devoluções           : {dados_empresa['valor_de_devolucao']:,.2f}\n")
                arquivo_txt.write("\n" + "-" * 80 + "\n\n")
                
                arquivo_txt.write(">> Apuração de PIS e COFINS :\n")
                arquivo_txt.write(f"   - Gastos com Insumos (Base Crédito)    : {round(dados_empresa['credito_por_entradas_pis_cofins'], 2):,.2f}\n")
                arquivo_txt.write(f"   - Devoluções (Base Crédito)            : {round(dados_empresa['credito_por_entradas_pis_cofins_devolucao'], 2):,.2f}\n")
                arquivo_txt.write(f"   - Gastos com transporte (Base Crédito) : {round(dados_empresa['credito_por_entradas_cte_pis_cofins'], 2):,.2f}\n")
                # arquivo_txt.write(f"   - Base de credito total de PIS e COFINS: {round(dados_empresa['base_credito_total_pis_cofins'], 2):,.2f}\n")
                # arquivo_txt.write(f"   - Base de debito original PIS e COFINS : {round(dados_empresa['base_original_pis_cofins'], 2):,.2f}\n")
                # arquivo_txt.write(f"   - Base de de PIS e COFINS Sem ICMS     : {round(dados_empresa['base_pis_cofins_sem_icms'], 2):,.2f}\n\n")
                
                arquivo_txt.write(f"   - CREDITO DE ICMS ST                   : {round(dados_empresa['credito_pis_cofins_icms_st'], 2):,.2f}\n")
                arquivo_txt.write(f"   - Base de de PIS e COFINS Sem ICMS ST  : {round(dados_empresa['base_pis_cofins_sem_icms_st'], 2):,.2f}\n\n")
                
                arquivo_txt.write(f"   - Saldo credor anterior PIS            : {round(dados_empresa['saldo_credor_anterior_pis'], 2):,.2f}\n")
                arquivo_txt.write(f"   - Crédito PIS                          : {round(dados_empresa['credito_pis_do_mes'], 2):,.2f}\n")
                arquivo_txt.write(f"   - Débito PIS                           : {round(dados_empresa['debito_pis_do_mes'], 2):,.2f}\n")
                arquivo_txt.write(f"   - Débito a Pagar PIS                   : {round(dados_empresa['debito_a_pagar_pis'], 2):,.2f}\n\n")
                
                arquivo_txt.write(f"   - Saldo credor anterior COFINS         : {round(dados_empresa['saldo_credor_anterior_cofins'], 2):,.2f}\n")
                arquivo_txt.write(f"   - Crédito COFINS                       : {round(dados_empresa['credito_cofins_do_mes'], 2):,.2f}\n")
                arquivo_txt.write(f"   - Débito COFINS                        : {round(dados_empresa['debito_cofins_do_mes'], 2):,.2f}\n")
                arquivo_txt.write(f"   - Débito a Pagar COFINS                : {round(dados_empresa['debito_a_pagar_cofins'], 2):,.2f}\n\n")
                 
                arquivo_txt.write(f"   - Débito a Pagar TOTAL                 : {round(dados_empresa['debito_a_pagar_total'], 2):,.2f}\n")
                arquivo_txt.write(f"   - Crédito Acumulado PIS                : {round(dados_empresa['credito_acumulado_pis'], 2):,.2f}\n")
                arquivo_txt.write(f"   - Crédito Acumulado COFINS             : {round(dados_empresa['credito_acumulado_cofins'], 2):,.2f}\n\n")
                
                arquivo_txt.write(">> Apuração de ICMS :\n")
                arquivo_txt.write(f"   - Saldo credor anterior                : {round(dados_empresa['saldo_credor_anterior'], 2):,.2f}\n")
                arquivo_txt.write(f"   - Base de calculo ICMS                 : {round(dados_empresa['base_icms'], 2):,.2f}\n\n")
                
                arquivo_txt.write(f"   - Crédito por entradas ICMS            : {round(dados_empresa['credito_por_entradas_icms'], 2):,.2f}\n")
                arquivo_txt.write(f"   - Crédito por CTE ICMS                 : {round(dados_empresa['credito_por_entradas_cte_icms'], 2):,.2f}\n")
                arquivo_txt.write(f"   - Crédito total ICMS                   : {round(dados_empresa['credito_total_icms'], 2):,.2f}\n\n")
                
                arquivo_txt.write(f"   - Débito por saidas ICMS               : {round(dados_empresa['debito_icms'], 2):,.2f}\n")
                arquivo_txt.write(f"   - Débito a pagar ICMS                  : {round(dados_empresa['debito_a_pagar_icms'], 2):,.2f}\n\n")
                
                arquivo_txt.write(f"   - Saldo Credor a transportar           : {round(dados_empresa['saldo_credor_a_transportar'], 2):,.2f}\n\n")
                arquivo_txt.write(f"   - Credito Acumulado ICMS               : {round(dados_empresa['credito_acumulado_icms'], 2):,.2f}\n")

                # --- Detalhamento dos CSTs CORRETOS ---
                arquivo_txt.write("\n>> Detalhamento dos CSTs (CORRETOS):\n")
                if dados_empresa['dicionario_csts_corretos']:
                    for cst, info in dados_empresa['dicionario_csts_corretos'].items():
                        arquivo_txt.write(f"   * CST: {cst}\n")
                        arquivo_txt.write("     - Aliquotas PIS:\n")
                        for aliquota, valor in info['aliquotas_pis'].items():
                            arquivo_txt.write(f"         > {aliquota}: {valor:,.2f}\n")
                        arquivo_txt.write("     - Aliquotas COFINS:\n")
                        for aliquota, valor in info['aliquotas_cofins'].items():
                            arquivo_txt.write(f"         > {aliquota}: {valor:,.2f}\n")
                        arquivo_txt.write("     - Base ICMS:\n")
                        arquivo_txt.write(f'         > {str(info['base_icms'])}')
                        arquivo_txt.write("\n")
                else:
                    arquivo_txt.write("   Nenhum CST CORRETO registrado.\n\n")
                
                # --- Resumo dos CSTs ORIGINAIS (opcional) ---
                arquivo_txt.write(">> Resumo dos CSTs ORIGINAIS (antes da correção):\n")
                if dados_empresa['dicionario_csts_originais']:
                    for cst, valor in dados_empresa['dicionario_csts_originais'].items():
                        arquivo_txt.write(f"   - {cst}: {valor:,.2f}\n")
                else:
                    arquivo_txt.write("   Nenhum CST ORIGINAL registrado.\n")
                
                arquivo_txt.write("\n" + "=" * 80 + "\n\n")