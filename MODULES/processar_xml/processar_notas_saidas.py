import zipfile
import xml.etree.ElementTree as ET
import os
from MODULES.utilitarios import extrair_valores_notas, extrair_formatar_data_nf, buscar_melhor_correspondencia_ncm, extrair_cst_csosn, validar_nota, verificar_participante
from MODULES.public import dados_por_periodo_e_cnpj, inicializar_dicionario_central_periodo_cnpj
from MODULES.extracao import extrair_dados_itens, extrair_valores_notas, extrair_dados_nota, extrair_dados_emitente, extrair_dados_destinatario
from MODULES.processar_xml.processar_notas_entradas import processar_nota_entrada_root, processar_notas_entrada

destinatarios_unicos = {}
cache_correspondencias_ncm = {}
ncm_nao_encontrados = [['NCM', 'NOME ITEM', 'NUMERO DA NOTA', 'DATA DE EMISSÃO', 'VALOR DO PRODUTO']]

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

def calcular_icms_valor_a_recuperar(dados_excel, frete_item, desconto_item, valor_icms_item_nota, valor_item_nota, uf_venda, outro, base_icms, data):
    dados_item = extrair_dados_excel(dados_excel, uf_venda)
    reducao_base_calculo_excel = dados_item[3]
    aliq_interna_excel = dados_item[2]
    cest_excel = dados_item[1]               

    ano = int(data.split('/')[2])
    if ano >= 2025 and aliq_interna_excel == 0.18:
        aliq_interna_excel = 20.00
        
    # VERIFICA SE O ITEM É SUBSTITUTO TRIBUTARIO E CASO SEJA ZERA O ICMS 
    if cest_excel != 0 :
        calculo_base_de_calculo = 0
        calculo_icms = 0
        valor_a_recuperar = float(valor_icms_item_nota)
    else: 
        calculo_base_de_calculo = base_icms * reducao_base_calculo_excel
        calculo_icms = calculo_base_de_calculo * float(str(aliq_interna_excel).replace(',', '.'))
        valor_a_recuperar = round(float(valor_icms_item_nota), 2) - round(float(calculo_icms)  ,2)
    return valor_a_recuperar, calculo_icms, calculo_base_de_calculo, reducao_base_calculo_excel, aliq_interna_excel, cest_excel

def formata_cst(cst_pis_correto):
    
    if cst_pis_correto == '01 - Operação Tributável com Alíquota Básica':
        cst_pis_correto = '01'
    elif cst_pis_correto == '02 - Operação Tributável com Alíquota Diferenciada':
        cst_pis_correto = '02'
    elif cst_pis_correto == '03 - Operação Tributável com Alíquota por Unidade de Medida de Produto':
        cst_pis_correto = '03'
    elif cst_pis_correto == '04 - Operação Tributável Monofásica - Revenda a Alíquota Zero':
        cst_pis_correto = '04'
    elif cst_pis_correto == '05 - Operação Tributável por Substituição Tributária':
        cst_pis_correto = '05'
    elif cst_pis_correto == '06 - Operação Tributável a Alíquota Zero':
        cst_pis_correto = '06'    
    elif cst_pis_correto == '07 - Operação Isenta da Contribuição':
        cst_pis_correto = '07'
    elif cst_pis_correto == '08 - Operação sem Incidência da Contribuição':
        cst_pis_correto = '08'
    elif cst_pis_correto == '09 - Operação com Suspensão da Contribuição':
        cst_pis_correto = '09'
    elif cst_pis_correto == '49 - Outras Operações de Saída':
        cst_pis_correto = '49'

    return cst_pis_correto

def acumular_valor_por_cst(dados_empresa: dict, cst_pis_correto: str, valor_item_nota: float):
    """
    Soma o valor_item_nota no campo correspondente do dicionário dados_empresa
    com base no código CST informado.

    Exemplo:
        acumular_valor_por_cst(dados_empresa, '01', 150.0)
    """
    chave = f"valor_total_base_{cst_pis_correto.zfill(2)}"
    if chave not in dados_empresa:
        dados_empresa[chave] = 0.0
    dados_empresa[chave] += valor_item_nota

def processar_notas_saida(nome_arquivo_zip):
    with zipfile.ZipFile(os.path.join('notas_fiscais', nome_arquivo_zip), 'r') as arquivo_zip:
        lista_de_arquivos = [f for f in arquivo_zip.namelist() if not f.startswith('CANCELADO')]
        
        for arquivo_nome in lista_de_arquivos:
            dados_items = []
            try:
                with arquivo_zip.open(arquivo_nome) as arquivo_xml:
                    tree = ET.parse(arquivo_xml)
                    root = tree.getroot()

                    dados_empresa_emitente = root.find('.//{http://www.portalfiscal.inf.br/nfe}emit') 
                    dados_emitente = extrair_dados_emitente(dados_empresa_emitente)

                    dados_empresa_destinatario = root.find('.//{http://www.portalfiscal.inf.br/nfe}dest') 
                    dados_destinatario, cnpj_destinatario = extrair_dados_destinatario(dados_empresa_destinatario, destinatarios_unicos)
                    codigo_participante = cnpj_destinatario

                    chave_nota = root.find('.//{http://www.portalfiscal.inf.br/nfe}chNFe')
                    chave_nota = chave_nota.text if chave_nota is not None else '0'

                    dados_nota_fiscal = extrair_dados_nota(root, chave_nota, cnpj_destinatario)
                    dados_nota_fiscal['indicador_operacao'] = '1'

                    dados_datas = extrair_formatar_data_nf(root)
                    mes_ano = dados_datas['mes_ano']
                    data_emissao_formatada_nota = dados_datas['data_emissao_formatada_nota']
                    
                    if validar_nota(chave_nota, dados_nota_fiscal['finalidade_nfe']):
                        inicializar_dicionario_central_periodo_cnpj(mes_ano, dados_emitente['cnpj'])
            
                        dados_empresa = dados_por_periodo_e_cnpj[mes_ano]
                        
                        items = root.findall('.//{http://www.portalfiscal.inf.br/nfe}det')
                        dados_items, _ = extrair_dados_itens(items, chave_nota, dados_datas)
                        
                        tem_cfop_entrada = any(str(item['cfop'])[0] in ('1', '2', '3') for item in dados_items)
                        if tem_cfop_entrada:
                            processar_nota_entrada_root(root, True)
                            continue  # pula para a próxima nota

                        
                        for item in dados_items:
                            ncm_item_nota = item['ncm']
                            nome_item_nota = item['nome_item_nota']
                            codigo_item_nota = item['codigo_item_nota']
                            unidade_item_nota = item['unidade']
                            cest_item_nota = item['cest']
                            valor_item_nota = item['valor']
                            valor_bc_icms = item['base_calculo_icms']
                            aliq_icms_item_nota = item['aliq_icms']
                            valor_icms_item_nota = item['valor_icms'].replace(',', '.')
                            desconto_item_nota = item['desconto_item_nota']
                            outro_valor_item = item['outro_valor_item']
                            situacao_tributaria_icms = item['cst_icms']
                            dados_empresa['valor_total_nfe'] += float(valor_item_nota)

                            if ncm_item_nota not in cache_correspondencias_ncm:
                                cache_correspondencias_ncm[ncm_item_nota] = buscar_melhor_correspondencia_ncm(ncm_item_nota, nome_item_nota)
                            melhor_correspondencia, dados_analise_tributaria = cache_correspondencias_ncm[ncm_item_nota]

                            if melhor_correspondencia:
                                cst_icms_correto = melhor_correspondencia['cst_icms']

                                valor_a_recuperar_icms, debito_icms, base_icms, reducao_base_calculo_excel, aliq_interna_excel, cest_excel = calcular_icms_valor_a_recuperar(dados_analise_tributaria, dados_nota_fiscal['valor_frete'], desconto_item_nota, valor_icms_item_nota, valor_item_nota, dados_destinatario['uf'], float(outro_valor_item), valor_item_nota, dados_datas['data_emissao_formatada_nota_para_excel'])
                                dados_empresa['debito_icms'] += debito_icms
                                dados_empresa['base_icms'] += base_icms
                                dados_empresa['valor_a_recuperar_icms'] += valor_a_recuperar_icms

                                if valor_a_recuperar_icms > 0.2 :
                                    dados_empresa['unidades'].add(unidade_item_nota)
                                    if str(dados_nota_fiscal['modelo']) == '65':
                                        dados_empresa['itens_bloco_e'].append(f'|E113||{dados_nota_fiscal['modelo']}|{dados_nota_fiscal['serie']}||{dados_nota_fiscal['numero']}|{data_emissao_formatada_nota}|{codigo_item_nota}|{str(round(valor_a_recuperar_icms, 2)).replace('.',',')}|{chave_nota}|')
                                            
                                        if cest_item_nota != '' and cest_item_nota != 0:
                                            dados_empresa['itens_bloco_0200'].append(f'|0200|{codigo_item_nota}|{nome_item_nota}|||{unidade_item_nota}|00|{ncm_item_nota}||85||{str(round(float(aliq_icms_item_nota))).replace('.',',')}|{cest_item_nota}|')
                                        else : 
                                            dados_empresa['itens_bloco_0200'].append(f'|0200|{codigo_item_nota}|{nome_item_nota}|||{unidade_item_nota}|00|{ncm_item_nota}||85||{str(round(float(aliq_icms_item_nota))).replace('.',',')}||')

                                    elif str(dados_nota_fiscal['modelo']) == '63':
                                        dados_empresa['itens_bloco_e'].append(f'|E113||{dados_nota_fiscal['modelo']}|{dados_nota_fiscal['serie']}||{dados_nota_fiscal['numero']}|{data_emissao_formatada_nota}||{str(round(valor_a_recuperar_icms, 2)).replace('.',',')}|{chave_nota}|')
                                            
                                        if cest_item_nota != '' and cest_item_nota != 0:
                                            dados_empresa['itens_bloco_0200'].append(f'|0200|{codigo_item_nota}|{nome_item_nota}|||{unidade_item_nota}|00|{ncm_item_nota}||85||{str(round(float(aliq_icms_item_nota))).replace('.',',')}|{cest_item_nota}|')
                                        else : 
                                            dados_empresa['itens_bloco_0200'].append(f'|0200|{codigo_item_nota}|{nome_item_nota}|||{unidade_item_nota}|00|{ncm_item_nota}||85||{str(round(float(aliq_icms_item_nota))).replace('.',',')}||')

                                    elif str(dados_nota_fiscal['modelo']) == '55':
                                        dados_empresa['itens_bloco_e'].append(f'|E113|{verificar_participante(codigo_participante, mes_ano)}|{dados_nota_fiscal['modelo']}|{dados_nota_fiscal['serie']}||{dados_nota_fiscal['numero']}|{data_emissao_formatada_nota}|{codigo_item_nota}|{str(round(valor_a_recuperar_icms, 2)).replace('.',',')}|{chave_nota}|')         
                                        if cest_item_nota != '' and cest_item_nota != 0:
                                            dados_empresa['itens_bloco_0200'].append(f'|0200|{codigo_item_nota}|{nome_item_nota}|||{unidade_item_nota}|00|{ncm_item_nota}||85||{str(round(float(aliq_icms_item_nota))).replace('.',',')}|{cest_item_nota}|')
                                        else :dados_empresa['itens_bloco_0200'].append(f'|0200|{codigo_item_nota}|{nome_item_nota}|||{unidade_item_nota}|00|{ncm_item_nota}||85||{str(round(float(aliq_icms_item_nota))).replace('.',',')}||')

                                    dados_empresa['qtd_itens_errados'] += 1
                                    dados_empresa['soma_valores_a_recuperar_icms'] += valor_a_recuperar_icms 
                                    
                                    dados_empresa['itens_a_recuperar_icms'].append({
                                        'chave_nota' : chave_nota,
                                        'cnpj_emitente' : dados_emitente['cnpj'],
                                        'nome_item_nota' : nome_item_nota,
                                        'codigo_item_nota' : codigo_item_nota,
                                        'unidade_item_nota' : unidade_item_nota,
                                        'ncm_item_nota' : ncm_item_nota,
                                        'cest_item_nota' : cest_item_nota,
                                        'situacao_tributaria_icms_nota' : situacao_tributaria_icms,
                                        'valor_item' : valor_item_nota,
                                        'base_icms_nota' : valor_bc_icms,
                                        'aliq_icms_item_nota' : aliq_icms_item_nota,
                                        'valor_icms_item_nota' : valor_icms_item_nota,
                                        'cest_reapurado' : cest_excel,
                                        'reducao_base_calculo_reapurada' : reducao_base_calculo_excel,
                                        'base_icms_reapurada' : base_icms,
                                        'aliq_interna_reapurada' : aliq_interna_excel,
                                        'debito_icms_reapurado' : debito_icms,
                                        'valor_a_recuperar' : valor_a_recuperar_icms
                                    })
                                
                                cst_pis_correto = formata_cst(melhor_correspondencia['cst_pis_cofins'])
                                aliquota_pis_correta = melhor_correspondencia['aliquota_pis']
                                aliquota_cofins_correta = melhor_correspondencia['aliquota_cofins']

                                if cst_pis_correto == '01':
                                    dados_empresa['debito_icms_retirar_base_pis_cofins'] += debito_icms
                                    base_calculo_pis_correto = item['valor_base_calculado'] - debito_icms 
                                    base_calculo_cofins_correto = item['valor_base_calculado'] - debito_icms 
                                    if base_calculo_pis_correto < 0 :
                                        base_calculo_pis_correto = 0
                                    if base_calculo_cofins_correto < 0 :
                                        base_calculo_cofins_correto = 0
                                            
                                else :
                                    base_calculo_pis_correto = item['valor_base_calculado']
                                    base_calculo_cofins_correto = item['valor_base_calculado']
                                
                                
                                valor_pis_correto = round(base_calculo_pis_correto * aliquota_pis_correta, 2)   
                                valor_cofins_correto = round(base_calculo_cofins_correto * aliquota_cofins_correta, 2)

                                item['cst_pis_correto'] = cst_pis_correto
                                item['cst_cofins_correto'] = cst_pis_correto
                                item['cst_icms_correto'] = cst_icms_correto
                                item['aliquota_pis_correto'] = round(aliquota_pis_correta * 100, 2)
                                item['aliquota_cofins_correto'] = round(aliquota_cofins_correta * 100, 2)
                                item['base_calculo_pis_correto'] = base_calculo_pis_correto
                                item['valor_pis_correto'] = valor_pis_correto
                                item['base_calculo_cofins_correto'] = base_calculo_cofins_correto
                                item['valor_cofins_correto'] = valor_cofins_correto
                                
                                acumular_valor_por_cst(dados_empresa, cst_pis_correto, valor_item_nota)
                            else:
                                ncm_nao_encontrados.append([ncm_item_nota, nome_item_nota, chave_nota, dados_datas['data_emissao_formatada_nota_para_excel'], valor_item_nota])
                                item['cst_pis_correto'] = '01'
                                item['cst_cofins_correto'] = '01'
                                item['aliquota_pis_correto'] = 1.65
                                item['aliquota_cofins_correto'] = 7.60
                                item['base_calculo_pis_correto'] = base_calculo_pis_correto
                                item['valor_pis_correto'] = valor_pis_correto
                                item['base_calculo_cofins_correto'] = base_calculo_cofins_correto
                                item['valor_cofins_correto'] = valor_cofins_correto
                                
                            dados_empresa['itens'].extend(dados_items)
                            dados_nota_fiscal['itens'] = dados_items
                            dados_empresa['num_itens_processados'] += 1
                        
                        dados_empresa['num_notas_saida'] += 1
                        dados_empresa['razao_social'] = dados_emitente['razao_social']
                        dados_empresa['notas'].append(dados_nota_fiscal)
                        dados_empresa['emitente'] = dados_emitente
                        dados_empresa['participantes'][cnpj_destinatario] = dados_destinatario
            except ET.ParseError as e:
                print(f"Erro ao processar o arquivo XML {arquivo_nome}: {e}")