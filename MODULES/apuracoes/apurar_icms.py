def apurar_icms(dados_por_periodo_e_cnpj):
    credito_acumulado_icms = 0
    for periodo in sorted(dados_por_periodo_e_cnpj.keys()):
        for cnpj in dados_por_periodo_e_cnpj[periodo]:
            dados_empresa = dados_por_periodo_e_cnpj[periodo]
            
            dados_empresa['saldo_credor_anterior'] = credito_acumulado_icms
            
            credito_icms_no_mes = dados_empresa['credito_por_entradas_icms'] + dados_empresa['credito_por_entradas_cte_icms']
            debito_a_pagar_icms = dados_empresa['debito_icms'] - credito_icms_no_mes
            saldo_credor = 0        
            if debito_a_pagar_icms <= 0:
                saldo_credor = credito_icms_no_mes - dados_empresa['debito_icms']
                credito_acumulado_icms += -debito_a_pagar_icms
                debito_a_pagar_icms = 0
            elif debito_a_pagar_icms > 0:
                if credito_acumulado_icms >= debito_a_pagar_icms:
                    credito_acumulado_icms -= debito_a_pagar_icms
                    debito_a_pagar_icms = 0
                elif credito_acumulado_icms < debito_a_pagar_icms:
                    debito_a_pagar_icms -= credito_acumulado_icms
                    credito_acumulado_icms = 0

            dados_empresa['saldo_credor_a_transportar'] = saldo_credor
            dados_empresa['debito_a_pagar_icms'] = debito_a_pagar_icms
            dados_empresa['credito_acumulado_icms'] = credito_acumulado_icms
            dados_empresa['credito_total_icms'] = credito_icms_no_mes

def extrair_dados_excel(melhor_correspondencia, uf_venda):
    ncm_excel = melhor_correspondencia['NCM']
    aliq_interna_excel = melhor_correspondencia['ALIQUOTA ICMS RETORNADO']
    rbc_interestadual = melhor_correspondencia['ALIQUOTA REDUCAO EXTERNA']
    rbc_excel = melhor_correspondencia['ALIQUOTA REDUCAO INTERNA']
    cest_excel = str(melhor_correspondencia['CEST']).replace('.','').strip()
    
    if cest_excel == 'NÃO TEM ST':
        cest_excel = 0
        tem_st = False
    else :
        cest_excel = int(cest_excel)
        tem_st = True
    
    if uf_venda != 'DF':
        aliq_interna_excel = 0.12
        rbc_excel = rbc_interestadual
    
    if rbc_excel.strip() != 'NÃO TEM REDUÇÃO' and rbc_excel.strip() != 'NÃO TEM REDUÇÃO INTERESTADUAL':
        reducao_base_calculo_excel = float(rbc_excel.replace('%','').replace(',', '.')) / 100
    else: 
        reducao_base_calculo_excel = 1 
    
    return [ncm_excel, cest_excel, aliq_interna_excel, reducao_base_calculo_excel, tem_st, 'exige_estorno', 'chave_compra', 'numero_item_compra']