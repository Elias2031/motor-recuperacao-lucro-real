import os 
from MODULES.processar_xml.processar_notas_saidas import processar_notas_saida
from MODULES.processar_xml.processar_notas_entradas import processar_notas_entrada
from MODULES.processar_xml.processar_notas_entradas_cte import processar_notas_entrada_cte
from MODULES.relatorios.gerar_apuracao_consolidada import gerar_planilha_apuracao_consolidada
from MODULES.relatorios.gerar_relatorio_padrão import gerar_relatorios_mensais_padrao
from MODULES.relatorios.gerar_relatorios_mensais import gerar_relatorios_mensais
from MODULES.relatorios.gerar_planilha_ncm_nao_encontrados import gerar_planilha_ncm_nao_encontrados
from MODULES.relatorios.gerar_planilhas_itens_credito_icms import gerar_planilha_itens_credito_icms
from MODULES.apuracoes.apurar_pis_cofins import apurar_pis_cofins, gerar_relatorio_apuracao_pis_cofins
from MODULES.public import dados_por_periodo_e_cnpj
from MODULES.speds.processar_sped import processar_speds
from MODULES.speds.processar_sped_contribuicoes import gerar_arquivo_sped
import traceback

def executar_com_debug(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception:
        traceback.print_exc()   # mostra o local exato do crash (arquivo/linha)
        raise

def converter_sets_para_listas(dado):
    if isinstance(dado, set):
        return list(dado)  # Converte set para lista
    elif isinstance(dado, dict):
        return {chave: converter_sets_para_listas(valor) for chave, valor in dado.items()}
    elif isinstance(dado, list):
        return [converter_sets_para_listas(item) for item in dado]
    return dado

def comecar_apurar():
    diretorio_atual = os.getcwd()
    arquivos_na_pasta_notas_fiscais = os.listdir(os.path.join(diretorio_atual, 'notas_fiscais'))
    arquivos_zip = [arquivo for arquivo in arquivos_na_pasta_notas_fiscais if arquivo.endswith('.zip')]
    
    for nome_arquivo_zip in arquivos_zip:
        
        if 'cte'in nome_arquivo_zip.lower():
            processar_notas_entrada_cte(nome_arquivo_zip)

        elif 'dest' in nome_arquivo_zip.lower() or 'destinatário' in nome_arquivo_zip.lower():
            processar_notas_entrada(nome_arquivo_zip)
        
        else:
            processar_notas_saida(nome_arquivo_zip)                    

    print('GERANDO PLANILHA DE NCMS NÃO ENCONTRADOS')
    gerar_planilha_ncm_nao_encontrados()
    
    print('RETIFICANDO ARQUIVOS SPED')
    processar_speds(dados_por_periodo_e_cnpj)
    
    print('APURANDO PIS E COFINS')
    apurar_pis_cofins(dados_por_periodo_e_cnpj)
    
    # 2. Gera os relatórios detalhados para cada empresa e período
    gerar_relatorio_apuracao_pis_cofins(dados_por_periodo_e_cnpj)
    
    print('GERANDO SPED CONTRIBUIÇÕES')    
    gerar_arquivo_sped(dados_por_periodo_e_cnpj)

    print('GERANDO RELATORIOS MENSAIS')

    executar_com_debug(gerar_relatorios_mensais, dados_por_periodo_e_cnpj)

    print('GERANDO RELATORIOS MENSAIS')
    gerar_relatorios_mensais_padrao(dados_por_periodo_e_cnpj)
    
    print('GERANDO PLANILHA DE APURAÇÃO CONSOLIDADE')
    gerar_planilha_apuracao_consolidada(dados_por_periodo_e_cnpj)
    
    print('GERANDO PLANILHAS DE CREDITO')
    gerar_planilha_itens_credito_icms(dados_por_periodo_e_cnpj)
    print('APURAÇÃO FINALIZADA!')
    
comecar_apurar()