from MODULES.public import notas_processadas
import pandas as pd # type: ignore
import datetime
import re
import os
from pathlib import Path
import re
from typing import Optional

diretorio_atual = os.getcwd()
arquivos_na_pasta_analise = os.listdir(os.path.join(diretorio_atual, 'ANALISE'))
analise = pd.read_excel(os.path.join(diretorio_atual, 'ANALISE', arquivos_na_pasta_analise[0]))

def normaliza_aliquota(aliquota):
    """Normaliza a alíquota para decimal padronizado com 4 casas (ex: 1,65 → 0.0165)."""
    try:
        # converte vírgula para ponto e remove espaços
        aliq = str(aliquota).strip().replace(',', '.')
        valor = float(aliq)

        # se vier em formato percentual (ex: 1.65 ou 1,65), divide por 100
        # if valor > 1:
        #     valor /= 100

        return f"{valor:.2f}"  # retorna string com 4 casas
    except Exception:
        return "0.00"

def validar_nota(chave_nota, finalidade_nfe):
    # if finalidade_nfe != '1':
    #     return False
    
    if chave_nota in notas_processadas:
        return False

    notas_processadas.add(chave_nota)
    return True

def validar_nota_entrada(chave_nota):
    if chave_nota in notas_processadas:
        return False

    notas_processadas.add(chave_nota)
    return True
        
def extrair_valores_notas(root, caminho, valor_padrao):
    """Extrai um valor de um elemento XML, retornando um padrão se não encontrado."""
    elemento = root.find(f'.//{{http://www.portalfiscal.inf.br/nfe}}{caminho}')
    return elemento.text if elemento is not None else valor_padrao

def extrair_formatar_data_nf(root):
    # EXTRAIR E FORMATAR DATA DA NOTA
    data_emissao_nota = root.find('.//{http://www.portalfiscal.inf.br/nfe}dhEmi')
    data_emissao_nota = data_emissao_nota.text if data_emissao_nota is not None else '0'    
    if data_emissao_nota != '0':
        # Converter a string para um objeto datetime
        data_objeto = datetime.datetime.strptime(data_emissao_nota[:10], "%Y-%m-%d")
        
        # Formatar para exibição no Excel
        data_emissao_formatada_nota_para_excel = data_objeto.strftime("%d/%m/%Y")
        data_emissao_formatada_nota = data_objeto.strftime("%d%m%Y")
        
        # Extrair mês e ano
        mes = data_objeto.month
        mes = str(mes).zfill(2)
        ano = data_objeto.year
        
    else:
        data_emissao_formatada_nota_para_excel = '0'
        mes = '0'
        ano = '0'
    mes_ano = f'{ano}-{mes}'    
    dados_datas = {
        'data_emissao_formatada_nota' : data_emissao_formatada_nota,
        'data_emissao_formatada_nota_para_excel' : data_emissao_formatada_nota_para_excel,
        'mes_ano' : mes_ano
    }    
        
    return dados_datas

def extrair_cst_csosn(item):
    # EXTRAIR E FORMATAR SITAÇÃO TRIBUTARIA DO ICMS 
    icms = item.find('.//{http://www.portalfiscal.inf.br/nfe}ICMS')
    if icms is not None:
        cst_icms = icms.find('.//{http://www.portalfiscal.inf.br/nfe}CST').text if icms.find('.//{http://www.portalfiscal.inf.br/nfe}CST') is not None else 0
        csosn_imcs = icms.find('.//{http://www.portalfiscal.inf.br/nfe}CSOSN').text if icms.find('.//{http://www.portalfiscal.inf.br/nfe}CSOSN') is not None else 0
    else:
        cst_icms = 0
        
    try:
        if cst_icms == 0 :
                situacao_tributaria_icms = csosn_imcs
        else: 
            situacao_tributaria_icms = cst_icms
            
        return situacao_tributaria_icms
    except Exception as e :
        return ''

def jaccard_similarity(str1, str2):
    # Convert to lowercase and remove punctuation
    str1 = re.sub(r'[^\w\s]', '', str1.lower())
    str2 = re.sub(r'[^\w\s]', '', str2.lower())
    
    set1 = set(str1.split())
    set2 = set(str2.split())
    
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    
    return len(intersection) / len(union)

def verificar_se_e_comercializado(ncm):    
    # return True
    filtro = analise.loc[analise['NCM'].astype(str) == str(ncm)]
    if not filtro.empty:
        return True
    else: False
    
def buscar_melhor_correspondencia_ncm(ncm, descricao_item):
    # Filtra as linhas que possuem o NCM correspondente
    filtro = analise.loc[analise['NCM'].astype(str).str.zfill(8) == str(ncm)]
    
    # Inicializa a variável para armazenar a resposta mais similar
    resposta_mais_similar = filtro.iloc[0] if not filtro.empty else None
    
    # Verifica se o filtro não está vazio
    if not filtro.empty:
        maior_similaridade = -1
        resposta_mais_similar = None

        # Itera sobre os candidatos do filtro
        for _, candidato in filtro.iterrows():
            descricao_excel = candidato['NOME ITEM']
            
            # Calcula a similaridade usando a métrica de Jaccard
            similaridade = jaccard_similarity(descricao_excel, descricao_item) * 100
            
            # Se a similaridade for maior que a maior já encontrada, atualiza
            if similaridade > maior_similaridade:
                maior_similaridade = similaridade
                resposta_mais_similar = candidato

                # Se a similaridade for maior que 70%, interrompe o loop
                if similaridade > 70:
                    break

        # Caso uma resposta tenha sido encontrada
        if resposta_mais_similar is not None:
            tributos_ncm = resposta_mais_similar
            
            # Extrai as opções de ICMS e PIS COFINS
            cst_icms = tributos_ncm['CST ICMS']
            opcoes_cst_icms = cst_icms.split('ou')
            
            cst_simples_pis_cofins = tributos_ncm['CST PIS']
            opcoes_pis_cofins = cst_simples_pis_cofins
            
            aliquota_pis = tributos_ncm['ALIQUOTA PIS']
            aliquota_cofins = tributos_ncm['ALIQUOTA COFINS']

            # Ajusta as opções de PIS COFINS, se necessário
            if cst_simples_pis_cofins == '49 - Outras Operações de Saída ou 99 - Outras Operações':
                opcoes_pis_cofins = '49 ou 99'
            
            # Prepara os dados para retorno
            dados_ncm = {
                'opcoes_icms': opcoes_cst_icms,
                'opcoes_pis_cofins': opcoes_pis_cofins,
                'opcoes_cfop': '5102 ou 5102',
                'cst_icms': cst_icms,
                'cst_pis_cofins': cst_simples_pis_cofins,
                'aliquota_pis': float(aliquota_pis),
                'aliquota_cofins': float(aliquota_cofins)
            }
            
            return dados_ncm, resposta_mais_similar
    
    
    else:
        # Caso o NCM não tenha sido encontrado
        # print(f'NCM NÃO ENCONTRADO => {ncm}, {descricao_item}')
        return None, None  # Adiciona o NCM à lista de NCMS não encontrados
    
def _so_digitos(s: str) -> str:
    return re.sub(r'\D+', '', s or '')

def _periodo_arquivo(nome: str) -> Optional[str]:
    """
    Extrai o período no formato MM_AAAA a partir das datas no nome do arquivo SPED.
    Exemplo: ...-20240701-20240731-... -> retorna '07_2024'
    """
    m = re.search(r'-(\d{8})-(\d{8})-', nome)
    if not m:
        return None
    data_ini = m.group(1)  # AAAAMMDD
    mes = data_ini[4:6]
    ano = data_ini[0:4]
    # print(f"{mes}_{ano}")
    return f"{ano}-{mes}"

def verificar_participante(cnpj_ou_cpf: str, mes_ano: str, pasta_sped: str = "SPED") -> Optional[str]:
    # print(mes_ano)
    """
    Busca o arquivo SPED do período (MM_AAAA), abre e procura o participante no registro |0150|.
    Retorna COD_PART se encontrar.
    """
    alvo_doc = _so_digitos(cnpj_ou_cpf)

    base = Path(pasta_sped)
    if not base.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {base.resolve()}")

    # Filtra arquivos do período
    candidatos = [p for p in base.iterdir() if p.is_file() and _periodo_arquivo(p.name) == mes_ano]

    if not candidatos:
        print(f"Nenhum arquivo SPED encontrado para o período {mes_ano}")
        return None

    # Dá prioridade para entrega '0' (original)
    candidatos.sort(key=lambda p: int(re.search(r'-(\d)-', p.name).group(1)) if re.search(r'-(\d)-', p.name) else 9)

    for arquivo in candidatos:
        try:
            with open(arquivo, 'r', encoding='utf-8', errors='ignore') as sped:
                for line in sped:
                    if not line.startswith('|0150|'):
                        continue
                    campos = line.rstrip('\n').split('|')
                    cnpj_part = _so_digitos(campos[5] if len(campos) > 5 else "")
                    cpf_part = _so_digitos(campos[6] if len(campos) > 6 else "")
                    if alvo_doc == cnpj_part or alvo_doc == cpf_part:
                        return campos[2] if len(campos) > 2 else None
                    else :
                        return 'MPH007'
                    
        except Exception as e:
            print(f"Erro lendo {arquivo.name}: {e}")

    print(f"Participante não encontrado no período {mes_ano} para {cnpj_ou_cpf}")
    return None