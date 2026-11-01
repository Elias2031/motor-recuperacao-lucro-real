import datetime
import PyPDF2
import os

from MODULES.utilitarios import extrair_cst_csosn 

def extrair_valores_notas(root, caminho, valor_padrao):
    """Extrai um valor de um elemento XML, retornando um padrão se não encontrado."""
    elemento = root.find(f'.//{{http://www.portalfiscal.inf.br/nfe}}{caminho}')
    return elemento.text if elemento is not None else valor_padrao

def extrair_dados_nota(root, chave, cnpj_destinatario):
    totais = root.find('.//{http://www.portalfiscal.inf.br/nfe}total')
    modelo = extrair_valores_notas(root, 'mod', None)
    if modelo == '65':
        dados_nota = {
            'modelo' : extrair_valores_notas(root, 'mod', None),
            'serie' : extrair_valores_notas(root, 'serie', None),
            'numero' : extrair_valores_notas(root, 'nNF', None),
            'data_emissao' : extrair_valores_notas(root, 'dhEmi', None),
            'valor_total' : extrair_valores_notas(root, 'vNF', None),
            'tipo_pagamento' : extrair_valores_notas(root, 'indPag', '0'),
            'valor_desconto' : extrair_valores_notas(totais, 'vDesc', None),
            'tipo_frete' : extrair_valores_notas(root, 'modFrete', None),
            'valor_frete' : extrair_valores_notas(totais, 'vFrete', None),
            'valor_seguro' : extrair_valores_notas(totais, 'vSeg', None),
            'valor_outros' : extrair_valores_notas(totais, 'vOutro', None),
            'valor_bc_icms' : extrair_valores_notas(totais, 'vBC', None),
            'valor_icms' : extrair_valores_notas(totais, 'vICMS', None),
            'valor_bc_icms_st' : extrair_valores_notas(totais, 'vBCST', None),
            'valor_icms_st' : extrair_valores_notas(totais, 'vST', None),
            'valor_ipi' : extrair_valores_notas(totais, 'vIPI', None),
            'valor_pis' : extrair_valores_notas(totais, 'vPIS', None),
            'valor_cofins' : extrair_valores_notas(totais, 'vCOFINS', None),
            'valor_pis_st' : extrair_valores_notas(totais, 'vPISST', ''),
            'valor_cofins_st' : extrair_valores_notas(totais, 'vCOFINSST', ''),
            'valor_mercadorias' : extrair_valores_notas(totais, 'vProd', ''),
            'chave' : chave,
            'cnpj_destinatario' : cnpj_destinatario,
            'natureza_operação' : extrair_valores_notas(root, 'natOp', ''),
            'finalidade_nfe' : extrair_valores_notas(root, 'finNFe', '1'),
            'informacoes_complementares' : extrair_valores_notas(root, 'infCpl', ''),
            'cnpj_emitente' : '',
        }
    else:
        dados_nota = {
            'modelo' : extrair_valores_notas(root, 'mod', None),
            'serie' : extrair_valores_notas(root, 'serie', None),
            'numero' : extrair_valores_notas(root, 'nNF', None),
            'data_emissao' : extrair_valores_notas(root, 'dhEmi', None),
            'valor_total' : extrair_valores_notas(root, 'vNF', None),
            'tipo_pagamento' : extrair_valores_notas(root, 'indPag', '0'),
            'valor_desconto' : extrair_valores_notas(root, 'vDesc', None),
            'tipo_frete' : extrair_valores_notas(root, 'modFrete', None),
            'valor_frete' : extrair_valores_notas(totais, 'vFrete', None),
            'valor_seguro' : extrair_valores_notas(totais, 'vSeg', None),
            'valor_outros' : extrair_valores_notas(totais, 'vOutro', None),
            'valor_bc_icms' : extrair_valores_notas(totais, 'vBC', None),
            'valor_icms' : extrair_valores_notas(totais, 'vICMS', None),
            'valor_bc_icms_st' : extrair_valores_notas(totais, 'vBCST', None),
            'valor_icms_st' : extrair_valores_notas(totais, 'vST', None),
            'valor_ipi' : extrair_valores_notas(totais, 'vIPI', None),
            'valor_pis' : extrair_valores_notas(totais, 'vPIS', None),
            'valor_cofins' : extrair_valores_notas(totais, 'vCOFINS', None),
            'valor_pis_st' : extrair_valores_notas(totais, 'vPISST', ''),
            'valor_cofins_st' : extrair_valores_notas(totais, 'vCOFINSST', ''),
            'valor_mercadorias' : extrair_valores_notas(totais, 'vProd', ''),
            'chave' : chave,''
            'cnpj_destinatario' : cnpj_destinatario,
            'natureza_operação' : extrair_valores_notas(root, 'natOp', ''),
            'finalidade_nfe' : extrair_valores_notas(root, 'finNFe', '1'),
            'informacoes_complementares' : extrair_valores_notas(root, 'infCpl', ''),
            'cnpj_emitente' : '',
        }
    
    
    return dados_nota

def extrair_dados_emitente(dados_empresa_emitente):
    if dados_empresa_emitente is not None:
        dados_emitente = {
            "razao_social": extrair_valores_notas(dados_empresa_emitente, 'xNome', None),
            "nome_fantasia": extrair_valores_notas(dados_empresa_emitente, 'xFant', None),
            "inscricao_estadual": extrair_valores_notas(dados_empresa_emitente, 'IE', None),
            "UF": extrair_valores_notas(dados_empresa_emitente, 'UF', None),
            "codigo_municipio": extrair_valores_notas(dados_empresa_emitente, 'cMun', None),
            "cnpj": extrair_valores_notas(dados_empresa_emitente, 'CNPJ', None),
            "cep": extrair_valores_notas(dados_empresa_emitente, 'CEP', None),
            "logradouro": extrair_valores_notas(dados_empresa_emitente, 'xLgr', None),
            "numero_logradouro": extrair_valores_notas(dados_empresa_emitente, 'nro', None),
            "bairro": extrair_valores_notas(dados_empresa_emitente, 'xBairro', None),
            "telefone": extrair_valores_notas(dados_empresa_emitente, 'fone', None),
            "codigo_pais": extrair_valores_notas(dados_empresa_emitente, 'cPais', ''),
        }
    else:
        dados_emitente = {
            "razao_social": None,
            "nome_fantasia": None,
            "inscricao_estadual": None,
            "UF": None,
            "codigo_municipio": None,
            "cnpj": None,
            "cep": None,
            "logradouro": None,
            "numero_logradouro": None,
            "bairro": None,
            "telefone": None,
            "codigo_pais": ''
        }

    return dados_emitente

def extrair_dados_destinatario(dados_empresa_destinatario, destinatarios_unicos):
    if dados_empresa_destinatario is not None:
        razao_social_destinatario = extrair_valores_notas(dados_empresa_destinatario, 'xNome', None)
        cnpj_destinatario = extrair_valores_notas(dados_empresa_destinatario, 'CNPJ', None)

        if cnpj_destinatario is None:
            cnpj_destinatario = extrair_valores_notas(dados_empresa_destinatario, 'CPF', None)

        dados_destinatario = {
            "razao_social": razao_social_destinatario,
            "codigo_pais": extrair_valores_notas(dados_empresa_destinatario, 'cPais', ''),
            "inscricao_estadual": extrair_valores_notas(dados_empresa_destinatario, 'IE', ''),
            "codigo_municipio": extrair_valores_notas(dados_empresa_destinatario, 'cMun', ''),
            "logradouro": extrair_valores_notas(dados_empresa_destinatario, 'xLgr', ''),
            "numero_logradouro": extrair_valores_notas(dados_empresa_destinatario, 'nro', ''),
            "bairro": extrair_valores_notas(dados_empresa_destinatario, 'xBairro', ''),
            "uf": extrair_valores_notas(dados_empresa_destinatario, 'UF', ''),
        }

        if cnpj_destinatario not in destinatarios_unicos:
            destinatarios_unicos[cnpj_destinatario] = dados_destinatario
            
        if razao_social_destinatario == 'CONSUMIDOR':
            
            dados_destinatario = {
                "razao_social": 'CONSUMIDOR FINAL PADRAO',
                "codigo_pais": '1058',
                "inscricao_estadual": '',
                "codigo_municipio": '5300108',
                "logradouro": 'BRASILIA',
                "numero_logradouro": 'S/N',
                "bairro": 'BRASILIA',
                "uf": 'DF',
            }    
        
    else:
        
        dados_destinatario = {
                "razao_social": 'CONSUMIDOR FINAL PADRAO',
                "codigo_pais": '1058',
                "inscricao_estadual": '',
                "codigo_municipio": '5300108',
                "logradouro": 'BRASILIA',
                "numero_logradouro": 'S/N',
                "bairro": 'BRASILIA',
                "uf": 'DF',
            }    
        cnpj_destinatario = ''
    return dados_destinatario, cnpj_destinatario

def extrair_dados_pgdas(diretorio_pgdas, pgdas):
    valor_rbt12 = 0
    contador_linhas_apos_total = 0     
    periodo = ''
    conteudo = ''
    valor_IRPJ_pago_original = ''
    valor_CSLL_pago_original = ''
    valor_COFINS_pago_original = ''
    valor_PIS_pago_original = ''
    valor_INSS_pago_original = ''
    valor_ICMS_pago_original = ''
    valor_IPI_pago_original = ''
    valor_ISS_pago_original = ''
    valor_DAS_pago_original = ''
    encontrou_total = False
    dados_pgdas = {}
    cnpj_encontrado = None
    receita_bruta_cnpj = None

    try:
        caminho_pdf = os.path.join(diretorio_pgdas, pgdas)
        with open(caminho_pdf, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            number_of_pages = len(reader.pages)
            valor_rbt12p = None
            for page_num in range(number_of_pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                conteudo += text
            
            # Processando o conteúdo extraído
            linhas = conteudo.splitlines()
            for linha in linhas:
                
                # Extração do período de apuração
                if linha.startswith('Período de Apuração'):
                    data_final = linha[33:44].replace('/', '').replace(" ", "")
                    ano = data_final[4:8]
                    mes = data_final[2:4]
                    periodo = f'{mes}_{ano}'
                
                if '(RBT12)' in linha:
                    dados_linha = linha.split()
                    rbt12 = dados_linha[2]
                    valor_rbt12 = float(rbt12[7:].replace('.', '').replace(',', '.'))
                
                if '(RBT12p)' in linha:
                    dados_linha = linha.split()
                    valor_rbt12p = dados_linha[3].split(')')[1]
                    if valor_rbt12p:
                        valor_rbt12 = float(valor_rbt12p.replace('.', '').replace(',', '.'))

                if encontrou_total:
                        contador_linhas_apos_total += 1
                        if contador_linhas_apos_total == 2:
                            valores_a_pagar_originais = linha.split(' ')
                            valor_IRPJ_pago_original = valores_a_pagar_originais[0]
                            valor_CSLL_pago_original = valores_a_pagar_originais[1]
                            valor_COFINS_pago_original = valores_a_pagar_originais[2]
                            valor_PIS_pago_original = valores_a_pagar_originais[3]
                            valor_INSS_pago_original = valores_a_pagar_originais[4]
                            valor_ICMS_pago_original = valores_a_pagar_originais[5]
                            valor_IPI_pago_original = valores_a_pagar_originais[6]
                            valor_ISS_pago_original = valores_a_pagar_originais[7]
                            valor_DAS_pago_original = valores_a_pagar_originais[8]
                    
                if 'Total do Débito Exigível (R$)' in linha:
                    encontrou_total = True
                    contador_linhas_apos_total = 0  # Reseta o contador após encontrar a linha alvo

                if 'CNPJ Estabelecimento' in linha:
                    cnpj_encontrado = linha.split(' ')[2].replace('.', '').replace('-', '').replace('/', '')
                
                # Se encontrar "Nenhuma atividade selecionada", ignora o CNPJ e seus dados
                if 'Nenhuma atividade selecionada' in linha:
                    if cnpj_encontrado in dados_pgdas:
                        del dados_pgdas[cnpj_encontrado]  # Remove qualquer dado já adicionado para o CNPJ
                    cnpj_encontrado = None
                    receita_bruta_cnpj = None
                    continue
                
                if 'Valor Informado' in linha :
                    receita_bruta_cnpj = linha.split(' ')[2].replace('.', '').replace(',', '.')

                if cnpj_encontrado and encontrou_total:
                    dados_pgdas[cnpj_encontrado] = {
                        'receita_bruta': float(receita_bruta_cnpj) if receita_bruta_cnpj else 0.0,
                        'valor_rbt12': float(valor_rbt12),
                        'periodo': periodo,
                        'valor_IRPJ_pago_original': valor_IRPJ_pago_original,
                        'valor_CSLL_pago_original': valor_CSLL_pago_original,
                        'valor_COFINS_pago_original': valor_COFINS_pago_original,
                        'valor_PIS_pago_original': valor_PIS_pago_original,
                        'valor_INSS_pago_original': valor_INSS_pago_original,
                        'valor_ICMS_pago_original': valor_ICMS_pago_original,
                        'valor_IPI_pago_original': valor_IPI_pago_original,
                        'valor_ISS_pago_original': valor_ISS_pago_original,
                        'valor_DAS_pago_original': valor_DAS_pago_original
                    }
                
                if 'Total Geral da Empresa' in linha:
                    return dados_pgdas

        return dados_pgdas
    except Exception as e:
        print(f'Erro ao processar o arquivo {pgdas}: {e}')

def extrair_formatar_data_nf(root):
    # EXTRAIR E FORMATAR DATA DA NOTA  
    data_emissao_nota = extrair_valores_notas(root, 'dhEmi', '0' )
    if data_emissao_nota != '0':
        # Converter a string para um objeto datetime
        data_objeto = datetime.datetime.strptime(data_emissao_nota[:10], "%Y-%m-%d")
        
        # Formatar para exibição no Excel
        data_emissao_formatada_nota_para_excel = data_objeto.strftime("%d/%m/%Y")
        
        # Extrair mês e ano
        mes = data_objeto.month
        mes = str(mes).zfill(2)
        ano = data_objeto.year
        mes_ano = f'{mes}_{ano}'
    else:
        data_emissao_formatada_nota_para_excel = '0'
        mes = '0'
        ano = '0'
        
    dados_datas = {
        'data_emissao_formatada_nota_para_excel' : data_emissao_formatada_nota_para_excel,
        'mes_ano' : mes_ano
    }    
        
    return dados_datas

def extrair_dados_itens(items, chave_nota, dados_datas):
    dados_itens = []
    valor_total_itens = 0
    for item in items:
        nome = extrair_valores_notas(item, 'xProd', 'ITEM IMPORTADO')
        ncm = extrair_valores_notas(item, 'NCM', None)
        cfop = extrair_valores_notas(item, 'CFOP', None)
        v_desc = float(extrair_valores_notas(item, 'vDesc', '0'))
        v_frete = float(extrair_valores_notas(item, 'vFrete', '0'))
        v_outro = float(extrair_valores_notas(item, 'vOutro', '0'))
        unidade = extrair_valores_notas(item, 'uCom', None)
        codigo_barras = extrair_valores_notas(item, 'cEAN', None)
        quantidade = extrair_valores_notas(item, 'qCom', None)
        valor_unitario = extrair_valores_notas(item, 'vUnCom', None)
        v_prod = float(extrair_valores_notas(item, 'vProd', '0'))
        cest = extrair_valores_notas(item, 'CEST', '')
        numero_item = item.attrib.get('nItem')
        cst_icms = extrair_cst_csosn(item)

        if cfop == "1202":
            cfop = '5102'

        valor_base = v_prod - v_desc + v_frete + v_outro
        valor_total_itens += float(valor_unitario)

        # --- ICMS ---
        icms = item.find('.//{http://www.portalfiscal.inf.br/nfe}ICMS')
        # cst_icms = extrair_valores_notas(icms, 'CST', '00') if icms is not None else '00'
        base_calculo_icms = extrair_valores_notas(icms, 'vBC', '0,00') if icms is not None else '0,00'
        aliq_icms = extrair_valores_notas(icms, 'pICMS', '0') if icms is not None else '0'
        valor_icms = extrair_valores_notas(icms, 'vICMS', '0,00') if icms is not None else '0,00'
        aliq_mva = extrair_valores_notas(icms, 'pMVAST', '0,00') if icms is not None else '0,00'
        bc_icms_st = extrair_valores_notas(icms, 'vBCST', '0,00') if icms is not None else '0,00'
        aliq_icms_st = extrair_valores_notas(icms, 'pICMSST', '0,00') if icms is not None else '0,00'
        valor_icms_st = extrair_valores_notas(icms, 'vICMSST', '0,00') if icms is not None else '0,00'
        origem_icms = extrair_valores_notas(icms, 'orig', '0,00') if icms is not None else '0,00'

        # --- IPI ---
        ipi = item.find('.//{http://www.portalfiscal.inf.br/nfe}IPI')
        cst_ipi = extrair_valores_notas(ipi, 'CST', '50') if ipi is not None else '50'
        base_calculo_ipi = extrair_valores_notas(ipi, 'vBC', '0,00') if ipi is not None else '0,00'
        aliq_ipi = extrair_valores_notas(ipi, 'pIPI', '0') if ipi is not None else '0'
        valor_ipi = extrair_valores_notas(ipi, 'vIPI', '0,00') if ipi is not None else '0,00'
        codigo_enquadramento_ipi = extrair_valores_notas(ipi, 'cEnq', '999') if ipi is not None else '999'

        # --- PIS ---
        pis = item.find('.//{http://www.portalfiscal.inf.br/nfe}PIS')
        cst_pis = extrair_valores_notas(pis, 'CST', '99') if pis is not None else '99'
        base_calculo_pis = extrair_valores_notas(pis, 'vBC', '0,00') if pis is not None else '0,00'
        aliq_pis = extrair_valores_notas(pis, 'pPIS', '0') if pis is not None else '0'
        valor_pis = extrair_valores_notas(pis, 'vPIS', '0,00') if pis is not None else '0,00'

        # --- COFINS ---
        cofins = item.find('.//{http://www.portalfiscal.inf.br/nfe}COFINS')
        cst_cofins = extrair_valores_notas(cofins, 'CST', '01') if cofins is not None else '01'
        base_calculo_cofins = extrair_valores_notas(cofins, 'vBC', '0,00') if cofins is not None else '0,00'
        aliq_cofins = extrair_valores_notas(cofins, 'pCOFINS', '0') if cofins is not None else '0'
        valor_cofins = extrair_valores_notas(cofins, 'vCOFINS', '0,00') if cofins is not None else '0,00'
        
        codigo_item_nota = extrair_valores_notas(item, 'cProd', '0')
                
        dados_itens.append({
            'nome_item_nota': nome,
            'chave_nota': chave_nota,
            'cst_icms': cst_icms,
            'cst_pis_cofins': cst_pis,
            'ncm': ncm,
            'cfop': cfop,
            'valor': v_prod,
            'data': dados_datas['data_emissao_formatada_nota_para_excel'],
            'codigo_barras': codigo_barras,
            'unidade': unidade,
            'cest' : cest,
            'outro_valor_item' : v_outro,

            'base_calculo_icms': base_calculo_icms,
            'aliq_icms': aliq_icms,
            'valor_icms': valor_icms,
            'aliq_mva' : aliq_mva,
            'bc_icms_st' : bc_icms_st,
            'aliq_icms_st' : aliq_icms_st,
            'valor_icms_st' : valor_icms_st,

            'cst_ipi': cst_ipi,
            'base_calculo_ipi': base_calculo_ipi,
            'aliq_ipi': aliq_ipi,
            'valor_ipi': valor_ipi,
            'codigo_enquadramento_ipi': codigo_enquadramento_ipi,

            'cst_pis': cst_pis,
            'base_calculo_pis': base_calculo_pis,
            'aliq_pis': aliq_pis,
            'valor_pis': valor_pis,

            'cst_cofins': cst_cofins,
            'base_calculo_cofins': base_calculo_cofins,
            'aliq_cofins': aliq_cofins,
            'valor_cofins': valor_cofins,
            'quantidade_item' : quantidade,
            'valor_unitario' : valor_unitario,
            'numero_item' : numero_item,
            'desconto_item_nota' : v_desc,
            'origem_icms' : origem_icms,
            'codigo_item_nota' : codigo_item_nota,
            'valor_frete_item' : v_frete,
            'valor_base_calculado' : valor_base
        })


    return dados_itens, valor_total_itens
