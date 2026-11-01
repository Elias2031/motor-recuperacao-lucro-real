import zipfile
import os
import xml.etree.ElementTree as ET
from MODULES.extracao import extrair_dados_destinatario, extrair_dados_emitente, extrair_dados_nota
from MODULES.utilitarios import buscar_melhor_correspondencia_ncm, extrair_cst_csosn, extrair_valores_notas, extrair_formatar_data_nf, verificar_se_e_comercializado, validar_nota_entrada
from MODULES.public import dados_por_periodo_e_cnpj, inicializar_dicionario_central_periodo_cnpj
destinatarios_unicos = {}

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
            'valor': valor_base,
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
        })


    return dados_itens, valor_total_itens

def processar_nota_entrada_root(root, nota_devolucao):
    """
    Processa UMA única NF-e de ENTRADA a partir de um ElementTree root já parseado.
    Essa função contém toda a lógica que antes ficava dentro do for do ZIP.
    """

    chave_nota = extrair_valores_notas(root, 'chNFe', '')
    finalidade_nfe = extrair_valores_notas(root, 'finNFe', '1')

    if not validar_nota_entrada(chave_nota):
        return  # não faz nada se a nota não for válida

    dados_datas = extrair_formatar_data_nf(root)
    mes_ano = dados_datas['mes_ano']

    dados_empresa_destinatario = root.find('.//{http://www.portalfiscal.inf.br/nfe}dest')
    _ , cnpj_destinatario = extrair_dados_destinatario(dados_empresa_destinatario,destinatarios_unicos)

    dados_empresa_emitente = root.find('.//{http://www.portalfiscal.inf.br/nfe}emit')
    dados_emitente = extrair_dados_emitente(dados_empresa_emitente)

    dados_nota_fiscal = extrair_dados_nota(root, chave_nota, cnpj_destinatario)
    dados_nota_fiscal['indicador_operacao'] = '0'
    dados_nota_fiscal['cnpj_emitente'] = dados_emitente['cnpj']

    # inicializa dict para o DESTINATÁRIO (entrada)
    if nota_devolucao :
        dados_nota_fiscal['indicador_emissao'] = '0' #EMISSAO PROPRIA
        inicializar_dicionario_central_periodo_cnpj(mes_ano, dados_nota_fiscal['cnpj_emitente'])
    else:
        inicializar_dicionario_central_periodo_cnpj(mes_ano, cnpj_destinatario)
        dados_empresa = dados_por_periodo_e_cnpj[mes_ano]
        dados_nota_fiscal['indicador_emissao'] = '1' #TERCEIROS
        

    items = root.findall('.//{http://www.portalfiscal.inf.br/nfe}det')
    dados_items, _ = extrair_dados_itens(items, chave_nota, dados_datas)

    for item in dados_items:

        if item['aliq_cofins'] == '7.65' or item['aliq_cofins'] == '7.6500':
            item['aliq_cofins'] = '7.60'

        if item['aliq_pis'] == '0.65' or item['aliq_pis'] == '0.6500':
            item['aliq_pis'] = '1.65'

        if item['aliq_cofins'] == '3.00' or item['aliq_cofins'] == '3.0000':
            item['aliq_cofins'] = '7.60'
         
        print(item['aliq_cofins'])
        print(item['aliq_pis'])

        cfop = item['cfop']

        if cfop[0] == "5":
            cfop = "1" + cfop[1:]
        elif cfop[0] == "6":
            cfop = "2" + cfop[1:]
        elif cfop[0] == "7":
            cfop = "3" + cfop[1:]

        if cfop == "1405":
            cfop = "1403"

        if cfop == "2929":  # 5929 e 6992 referenciam outras notas não devem ser creditadas ou debitadas
            cfop = "2949"
            # cfop = "1949"

        if cfop == "1667" or cfop == "1656":
            cfop = "1653"

        if cfop == '2106':
            cfop = '2102'

        if cfop == '1402':
            cfop = '1102'

        if cfop == '2108':
            cfop = '2102'

        if cfop == '2667':
            cfop = '2653'

        if cfop == '2656':
            cfop = '2653'

        if cfop == '1655':
            cfop = '2653'

        if cfop == '1915':
            cfop = '1933'

        if cfop == '1110':
            cfop = '1102'

        if cfop == '1929':
            cfop = '1949'
            item['cst_pis'] = '70'
            item['cst_cofins'] = '70'
        
        if cfop == '1401':
            cfop = '1403'
        
        if cfop == '2401':
            cfop = '2403'
        
        if cfop == '2101':
            cfop = '2102'
        
        if cfop == '1101':
            cfop = '1102'
            
        dados_ncm, resposta_mais_similar = buscar_melhor_correspondencia_ncm(
            item['ncm'],
            item['nome_item_nota']
        )   

        correspondencia_analise = dados_ncm is not None
        if not correspondencia_analise:
            # print(correspondencia_analise, cfop)    
            if cfop == '2102':
                cfop = '2556'
            if cfop == '1102':
                cfop = '1556'
            
                
            
            
        if nota_devolucao:
            item['cst_pis'] = '50'
            item['cst_cofins'] = '50'
                
        if item['cst_pis'] == '01':
            item['cst_pis_saida'] = '50'
            item['cst_cofins_saida'] = '50'

        elif item['cst_pis'] == '02':
            item['cst_pis_saida'] = '50'
            item['cst_cofins_saida'] = '50'

        elif item['cst_pis'] == '03':
            item['cst_pis_saida'] = '50'
            item['cst_cofins_saida'] = '50'

        elif item['cst_pis'] == '04':
            item['cst_pis_saida'] = '70'
            item['cst_cofins_saida'] = '70'

        elif item['cst_pis'] == '05':
            item['cst_pis_saida'] = '75'
            item['cst_cofins_saida'] = '75'

        elif item['cst_pis'] == '06':
            item['cst_pis_saida'] = '73'
            item['cst_cofins_saida'] = '73'

        elif item['cst_pis'] == '07':
            item['cst_pis_saida'] = '71'
            item['cst_cofins_saida'] = '71'

        elif item['cst_pis'] == '08':
            item['cst_pis_saida'] = '74'
            item['cst_cofins_saida'] = '74'

        elif item['cst_pis'] == '09':
            item['cst_pis_saida'] = '72'
            item['cst_cofins_saida'] = '72'

        elif item['cst_pis'] == '49':
            item['cst_pis_saida'] = '99'
            item['cst_cofins_saida'] = '99'
        else:
            item['cst_pis_saida'] = item['cst_pis']
            item['cst_cofins_saida'] = item['cst_cofins']

        item['cst_pis'] = item['cst_pis_saida']
        item['cst_cofins'] = item['cst_cofins_saida']
        item['cst_pis_correto'] = item['cst_pis_saida']
        item['cst_cofins_correto'] = item['cst_cofins_saida']
        item['base_calculo_pis_correto'] = item['base_calculo_pis']
        item['base_calculo_cofins_correto'] = item['base_calculo_cofins']
        item['aliquota_pis_correto'] = item['aliq_pis']
        item['aliquota_cofins_correto'] = item['aliq_cofins']
        item['valor_pis_correto'] = item['valor_pis']
        item['valor_cofins_correto'] = item['valor_cofins']
        item['cfop'] = cfop



        if finalidade_nfe == '4':
            dados_empresa['valor_de_devolucao'] += float(item['valor'])

        if item['ncm'] == '1918':
            dados_empresa['valor_de_devolucao'] += float(item['valor'])

        if item['valor_icms_st'] != '0,00':
            dados_empresa['credito_pis_cofins_icms_st'] += float(item['valor_icms_st'])
            dados_empresa['itens_que_geram_credito_pis_cofins_icms_st'].append({
                'nome_item_nota': item['nome_item_nota'],
                'valor_item': float(item['valor']),
                'ncm_item_nota': item['ncm'],
                'cfop_item_nota': item['cfop'],

                'valor_bc_icms': item['base_calculo_icms'],
                'valor_icms_item_nota': item['valor_icms'],

                'valor_icms_st': item['valor_icms_st'],

                'chave_nota': chave_nota,
                'data': mes_ano
            })
        
        dados_empresa['itens_compras'].append(item)
        dados_empresa['itens'].append(item)
        dados_empresa['num_itens_processados'] += 1

        dados_empresa['valor_total_nfe_entrada'] += float(
            item['base_calculo_pis'].replace(',', '.')
        )
        
    dados_empresa['num_notas_entrada'] += 1
    dados_empresa['participantes'][dados_emitente['cnpj']] = dados_emitente
    dados_empresa['notas'].append(dados_nota_fiscal)
    dados_nota_fiscal['itens'] = dados_items

def processar_notas_entrada(nome_arquivo_zip):
    with zipfile.ZipFile(os.path.join('notas_fiscais', nome_arquivo_zip), 'r') as arquivo_zip:
        lista_de_arquivos = [f for f in arquivo_zip.namelist() if not f.startswith('CANCELADO')]

        for arquivo_nome in lista_de_arquivos:
            try:
                with arquivo_zip.open(arquivo_nome) as arquivo_xml:
                    tree = ET.parse(arquivo_xml)
                    root = tree.getroot()
                    processar_nota_entrada_root(root, False)
            except ET.ParseError as e:
                print(f"Erro ao processar o arquivo XML de ENTRADA {arquivo_nome}: {e}")