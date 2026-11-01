import datetime
import zipfile
import os
import xml.etree.ElementTree as ET

from MODULES.public import inicializar_dicionario_central_periodo_cnpj, dados_por_periodo_e_cnpj

def extrair_formatar_data_nf_cte(root):
    # Extrair data de emissão
    data_emissao = root.find('.//{http://www.portalfiscal.inf.br/cte}dhEmi')
    data_emissao = data_emissao.text if data_emissao is not None else '0'
    
    if data_emissao != '0':
        data_emissao_obj = datetime.datetime.strptime(data_emissao[:10], "%Y-%m-%d")
        data_emissao_formatada = data_emissao_obj.strftime("%d/%m/%Y")
        mes = str(data_emissao_obj.month).zfill(2)
        ano = str(data_emissao_obj.year)
    else:
        data_emissao_formatada = '0'
        mes = '0'
        ano = '0'
    
    # Extrair data de recebimento
    data_recebimento = root.find('.//{http://www.portalfiscal.inf.br/cte}dhRecbto')
    data_recebimento = data_recebimento.text if data_recebimento is not None else '0'
    
    if data_recebimento != '0':
        data_recebimento_obj = datetime.datetime.strptime(data_recebimento[:10], "%Y-%m-%d")
        data_recebimento_formatada = data_recebimento_obj.strftime("%d/%m/%Y")
    else:
        data_recebimento_formatada = '0'
    
    # Montar retorno
    return {
        'data_recebimento_formatada_nota_para_excel': data_recebimento_formatada,
        'data_emissao_formatada_nota_para_excel': data_emissao_formatada,
        'mes_ano': f'{ano}-{mes}'
    }

def extrair_valores_notas_cte(root, caminho, valor_padrao):
    elemento = root.find(f'.//{{http://www.portalfiscal.inf.br/cte}}{caminho}')
    return elemento.text if elemento is not None else valor_padrao

def processar_notas_entrada_cte(nome_arquivo_zip):
    with zipfile.ZipFile(os.path.join('notas_fiscais', nome_arquivo_zip), 'r') as arquivo_zip:
        lista_de_arquivos = [f for f in arquivo_zip.namelist() if not f.startswith('CANCELADO')]

        for arquivo_nome in lista_de_arquivos:
            chave_nota = ''
            try:
                with arquivo_zip.open(arquivo_nome) as arquivo_xml:
                    tree = ET.parse(arquivo_xml)
                    root = tree.getroot()

                    dados_datas = extrair_formatar_data_nf_cte(root)
                    mes_ano = dados_datas['mes_ano']
                    data_emissao = dados_datas['data_emissao_formatada_nota_para_excel']
                    data_recebimento = dados_datas['data_recebimento_formatada_nota_para_excel']

                    chave_nota = extrair_valores_notas_cte(root, 'chCTe', '')
                    valor_icms_nota = extrair_valores_notas_cte(root, 'vICMS', 0)
                    valor_nota = extrair_valores_notas_cte(root, 'vTPrest', 0)
                    cod_uf = extrair_valores_notas_cte(root, 'cUF', 0)
                    cod_cte = extrair_valores_notas_cte(root, 'cCT', 0)
                    cfop = extrair_valores_notas_cte(root, 'CFOP', 0)
                    natureza_operacao = extrair_valores_notas_cte(root, 'natOp', 0)
                    modelo = extrair_valores_notas_cte(root, 'mod', 0)
                    numero_cte = extrair_valores_notas_cte(root, 'nCT', 0)
                    indicador_toma = extrair_valores_notas_cte(root, 'toma', 0)
                    serie = extrair_valores_notas_cte(root, 'serie', 0)
                    tipo_cte = extrair_valores_notas_cte(root, 'tpCTe', 0)
                    
                    if indicador_toma == '0':
                        indicador_frete = '1'
                        
                    elif indicador_toma == '1':
                        indicador_frete = '0'
                        
                    elif indicador_toma == '2':
                        indicador_frete = '1'
                    
                    elif indicador_toma == '3':
                        indicador_frete = '1'
                    
                    elif indicador_toma == '4':
                        indicador_frete = '2'
                    
                    bloco_destinatario = root.find('.//{http://www.portalfiscal.inf.br/cte}dest')
                    if bloco_destinatario is not None:
                        cnpj_destinatario = extrair_valores_notas_cte(bloco_destinatario, 'CNPJ', 0)
                        ie_destinatario = extrair_valores_notas_cte(bloco_destinatario, 'IE', 0)
                        razao_social_destinatario = extrair_valores_notas_cte(bloco_destinatario, 'xNome', 0)
                        logradouro_destinatario = extrair_valores_notas_cte(bloco_destinatario, 'xLgr', 0)
                        numero_endereco_destinatario = extrair_valores_notas_cte(bloco_destinatario, 'nro', 0)
                        bairro_destinatario = extrair_valores_notas_cte(bloco_destinatario, 'xBairro', 0)
                        cod_municipio_destinatario = extrair_valores_notas_cte(bloco_destinatario, 'cMun', 0)
                        uf_destinatario = extrair_valores_notas_cte(bloco_destinatario, 'UF', 0)
                        cod_pais_destinatario = extrair_valores_notas_cte(bloco_destinatario, 'cPais', 0)
                    # else:
                    #     print('DEBUG: BLOCO AUSENTE DESTINATARIO', chave_nota)
                    
                    bloco_emitente = root.find('.//{http://www.portalfiscal.inf.br/cte}emit')
                    if bloco_emitente is not None:
                        cnpj_emitente = extrair_valores_notas_cte(bloco_emitente, 'CNPJ', 0)
                        ie_emitente = extrair_valores_notas_cte(bloco_emitente, 'IE', 0)
                        razao_social_emitente = extrair_valores_notas_cte(bloco_emitente, 'xNome', 0)
                        logradouro_emitente = extrair_valores_notas_cte(bloco_emitente, 'xLgr', 0)
                        numero_endereco_emitente = extrair_valores_notas_cte(bloco_emitente, 'nro', 0)
                        bairro_emitente = extrair_valores_notas_cte(bloco_emitente, 'xBairro', 0)
                        cod_municipio_emitente = extrair_valores_notas_cte(bloco_emitente, 'cMun', 0)
                        uf_emitente = extrair_valores_notas_cte(bloco_emitente, 'UF', 0)
                        cod_pais_emitente = extrair_valores_notas_cte(bloco_emitente, 'cPais', '1058')
                    # else:
                    #     print('DEBUG: BLOCO AUSENTE EMITENTE', chave_nota)
                    
                    bloco_icms = root.find('.//{http://www.portalfiscal.inf.br/cte}ICMS')  
                    if bloco_icms is not None:
                        cst_icms = extrair_valores_notas_cte(bloco_icms, 'CST', 0)
                        base_icms = extrair_valores_notas_cte(bloco_icms, 'vBC', 0)
                        aliq_icms = extrair_valores_notas_cte(bloco_icms, 'pICMS', 0)
                        valor_icms = extrair_valores_notas_cte(bloco_icms, 'vICMS', 0)
                    # else :
                    #     print('DEBUG: BLOCO AUSENTE', chave_nota)
                    
                    inicializar_dicionario_central_periodo_cnpj(mes_ano, cnpj_destinatario)
                    dados_empresa = dados_por_periodo_e_cnpj[mes_ano]
                    dados_empresa['num_notas_entrada_cte'] += 1
                    
                    if indicador_toma == '3':
                        dados_empresa['credito_por_entradas_cte_pis_cofins'] += float(valor_nota)
                        dados_empresa['credito_por_entradas_cte_icms'] += float(valor_icms_nota)
                        
                        dados_empresa['cte_que_geram_credito'].append({
                            'chave' : chave_nota,
                            'valor_nota' : valor_nota,
                            'valor_icms_nota' : valor_icms_nota,
                            'indicador_toma' : indicador_toma
                        })
                        
                        
                    dados_empresa['entradas_cte'].append({
                        'chave_nota': chave_nota,
                        'valor_icms_nota': valor_icms_nota,
                        'valor_nota': valor_nota,
                        'cnpj_destinatario': cnpj_emitente,
                        'modelo' : modelo,
                        'serie' : serie,
                        'numero_cte' : numero_cte,
                        'data_emissao' : data_emissao,
                        'data_recebimento' : data_recebimento,
                        'tipo_cte' : tipo_cte,
                        'indicador_frete' : indicador_frete,
                        'indicador_toma' : indicador_toma,
                        'cst_icms' : cst_icms,
                        'base_icms' : base_icms,
                        'aliq_icms' : aliq_icms,
                        'valor_icms' : valor_icms,
                        'cod_cte' : cod_cte,
                        'cfop' : cfop,
                        'natureza_operacao' : natureza_operacao,
                        'cod_uf' : cod_uf,
                        
                    })
                    
                    dados_empresa['participantes'][cnpj_emitente] = {
                        'razao_social' : razao_social_emitente,
                        'codigo_pais' : cod_pais_emitente,
                        'inscricao_estadual' : ie_emitente,
                        'codigo_municipio' : cod_municipio_emitente,
                        'logradouro' : logradouro_emitente,
                        'numero_logradouro' : numero_endereco_emitente,
                        'bairro' : bairro_emitente,
                        'uf' : uf_emitente,
                    }
            
            except ET.ParseError as e:
                print(f"Erro ao processar o arquivo XML {arquivo_nome}: {e}")