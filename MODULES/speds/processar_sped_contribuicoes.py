from MODULES.config_ambiente import registro_0100
import os
import json
from datetime import datetime, timedelta
from functools import lru_cache
from MODULES.public import generos
from MODULES.utilitarios import jaccard_similarity, verificar_se_e_comercializado
global qtd_linhas_arquivo, contador_blocos
import pandas as pd
from collections import defaultdict
import re
from collections import defaultdict
from decimal import Decimal, getcontext, ROUND_DOWN
from MODULES.utilitarios import normaliza_aliquota
import calendar

registros_planilha = []

getcontext().prec = 28  # segurança p/ somas

contador_registros = {}
contador_blocos = {}
contador_csts = {}
qtd_linhas_arquivo = 0
naturezas = []
tipo_item_cache = {}
informacoes_complementares = []

ALIQ_PIS = '1,65'
ALIQ_COFINS = '7,60'

CFOP_REVENDA = {
    # compras p/ comercialização / revenda
    '1102', '2102',
    # ajustes/devoluções típicos que, no teu contexto, você pode tratar como revenda
    '1403', '2403', '1410', '2410', '1411', '2411'
}
CFOP_INSUMO = {
    # compras de insumos p/ industrialização / produção / prestação
    '1101', '2101', '1401', '2401'
}
CFOP_USO_CONSUMO = {
    # uso e consumo
    '1558', '2558', '1559', '2559'
}
CFOP_ATIVO_IMOB = {
    # ativo imobilizado
    '1551', '2551', '1552', '2552', '1556', '2556'
}
CFOP_ENERGIA = {
    # energia elétrica (ajuste conforme a tua base)
    '1253', '2253'
}
KW_REVENDA = [
    'revenda', 'mercadoria', 'produto acabado',
    'varejo', 'atacado', 'comercializacao'
]
KW_INSUMO = [
    'insumo', 'materia-prima', 'materia prima',
    'embalagem', 'etiqueta', 'filme stretch', 'fitilho',
    'aditivo', 'pigmento'
]
KW_USO_CONSUMO = [
    'uso e consumo', 'escritorio', 'papel a4', 'caneta', 'toner',
    'limpeza', 'detergente', 'desengraxante', 'luva descartavel',
    'epi', 'cafe', 'agua mineral'
]
KW_ENERGIA = [
    'energia', 'energia eletr', 'conta de luz'
    ]
KW_FRETE   = [
    'frete', 'ct-e', 'cte', 'transporte', 'servico de frete'
    ]
KW_IMOB    = [
    'maquina', 'equipamento', 'imobilizado', 'computador', 'impressora', 'servidor', 'veiculo'
    ]

CSTS_CREDITO_PIS = {'50','51','52','53','54','55','56','57','58','59','60','61','62','63','64','65','66'}
def fmt_br(valor):
    # float -> "1234,56" sem separador de milhar
    return f"{float(valor):,.2f}".replace(",", "").replace(".", ",")

# CST -> grupos (para detectar grupo 100/200/300)
MAP_CST_GRUPOS = {
    '50': (100,), '51': (200,), '52': (300,),
    '53': (100, 200), '54': (100, 300), '55': (200, 300),
    '56': (100, 200, 300),
    '60': (100,), '61': (200,), '62': (300,),
    '63': (100, 200), '64': (100, 300), '65': (200, 300),
    '66': (100, 200, 300),
}

# Grupo -> códigos de crédito possíveis (Tabela 4.3.6)
MAP_GRUPO_COD_CRED = {
    100: {
        '101': 'Crédito vinculado à receita tributada no mercado interno - Alíquota Básica',
        '102': 'Crédito vinculado à receita tributada no mercado interno - Alíquotas Diferenciadas',
        '103': 'Crédito vinculado à receita tributada no mercado interno - Alíquota por Unidade de Produto',
        '104': 'Crédito vinculado à receita tributada no mercado interno - Estoque de Abertura',
        '105': 'Crédito vinculado à receita tributada no mercado interno - Aquisição Embalagens para revenda',
        '106': 'Crédito vinculado à receita tributada no mercado interno - Presumido - agroindústria e aquisição combustível',
        '107': 'Crédito vinculado à receita tributada no mercado interno - Outros Créditos Presumidos',
        '108': 'Crédito vinculado à receita tributada no mercado interno - Importação',
        '109': 'Crédito vinculado à receita tributada no mercado interno - Atividade Imobiliária',
    },
    200: {
        '201': 'Crédito vinculado à receita não tributada no mercado interno - Alíquota Básica',
        '202': 'Crédito vinculado à receita não tributada no mercado interno - Alíquotas Diferenciadas',
        '203': 'Crédito vinculado à receita não tributada no mercado interno - Alíquota por Unidade de Produto',
        '204': 'Crédito vinculado à receita não tributada no mercado interno - Estoque de Abertura',
        '205': 'Crédito vinculado à receita não tributada no mercado interno - Aquisição Embalagens para revenda',
        '206': 'Crédito vinculado à receita não tributada no mercado interno - Presumido - agroindústria e aquisição combustível',
        '207': 'Crédito vinculado à receita não tributada no mercado interno - Outros Créditos Presumidos',
        '208': 'Crédito vinculado à receita não tributada no mercado interno - Importação',
    },
    300: {
        '301': 'Crédito vinculado à receita de exportação - Alíquota Básica',
        '302': 'Crédito vinculado à receita de exportação - Alíquotas Diferenciadas',
        '303': 'Crédito vinculado à receita de exportação - Alíquota por Unidade de Produto',
        '304': 'Crédito vinculado à receita de exportação - Estoque de Abertura',
        '305': 'Crédito vinculado à receita de exportação - Aquisição Embalagens para revenda',
        '306': 'Crédito vinculado à receita de exportação - Presumido - agroindústria e aquisição combustível',
        '307': 'Crédito vinculado à receita de exportação - Outros Créditos Presumidos',
        '308': 'Crédito vinculado à receita de exportação - Importação',
    },
}

def converter_data_para_mes_anterior_mmyyyy(data_str: str) -> str:
    """
    Converte uma data 'YYYY-MM' para o mês anterior no formato 'MMYYYY'.
    Exemplo: '2023-08' -> '072023'
    """
    data = datetime.strptime(data_str, "%Y-%m")
    # Retrocede 1 mês
    if data.month == 1:
        mes_anterior = 12
        ano_anterior = data.year - 1
    else:
        mes_anterior = data.month - 1
        ano_anterior = data.year
    return f"{mes_anterior:02d}{ano_anterior}"

def ultimo_dia_mes(periodo: str) -> str:
    """Retorna o último dia do mês no formato DDMMYYYY para período 'YYYY-MM'."""
    ano, mes = map(int, periodo.split('-'))
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return f"{ultimo_dia:02d}{mes:02d}{ano}"

def determinar_cod_nat_base_credito(item):
    """
    Determina o código NAT_BC_CRED de acordo com o CFOP do item.
    Salva os dados relevantes em registros_planilha (list[dict]) para geração posterior da planilha.
    """
    cfop = str(item.get('cfop', '')).strip()
    caminho_arquivo = './_RECURSOS_/cfop_creditos_pis_cofins_nat_operacao.txt'
    cod_nat = None

    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            for linha in arquivo:
                if not linha.strip() or linha.startswith('versão'):
                    continue

                campos = linha.strip().split('|')
                if len(campos) < 5:
                    continue

                cfop_linha = campos[0].strip()
                cod_nat_linha = campos[4].strip()

                if cfop_linha == cfop:
                    cod_nat = cod_nat_linha
                    break

    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        return None

    if not cod_nat:
        # print(f"⚠️ CFOP sem correspondência: {cfop}")
        return None

    # ---- Salva os dados do item ----
    registros_planilha.append({
        'chave_nfe': item.get('chave_nota', ''),
        'cfop': cfop,
        'descricao_item': item.get('nome_item_nota', ''),
        'valor': item.get('valor_item', 0.0),
        'cst_pis': item.get('cst_pis', ''),
        'aliquota_pis': item.get('aliq_pis', ''),
        'nat_bc_cred': cod_nat
    })

    return cod_nat

def to_decimal(v, default="0"):
    """Converte v em Decimal lidando com formatos pt-BR, strings vazias e símbolos."""
    if isinstance(v, Decimal):
        return v
    if v is None:
        return Decimal(default)
    if isinstance(v, (int, float)):
        return Decimal(str(v))

    s = str(v).strip()

    # valores "nulos" comuns
    if s == "" or s.lower() in {"nan", "none", "null"} or s in {"-", "—"}:
        return Decimal(default)

    # negativo com parênteses: (1.234,56)
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1].strip()

    # mantemos apenas dígitos e separadores .,-
    s = re.sub(r"[^0-9,.\-]", "", s)

    # decidir separador decimal
    if s.count(",") > 0 and s.count(".") > 0:
        # padrão BR: 1.234,56 -> remove pontos (milhar) e troca vírgula por ponto
        s = s.replace(".", "").replace(",", ".")
    elif s.count(",") > 0:
        # só vírgula -> assume decimal
        s = s.replace(".", "")  # se houver ponto perdido como milhar
        s = s.replace(",", ".")
    # senão, já está com ponto ou é inteiro

    if s in {"", "-", "."}:
        return Decimal(default)

    d = Decimal(s)
    if neg:
        d = -d
    return d

def gerar_bloco_9(arquivo):
    global qtd_linhas_arquivo
    qtd_registros_9900 = 0
    contar_e_escrever('|9001|0|', arquivo)
    
    for tipo_registro, quantidade in contador_registros.items():
        arquivo.write(f"|9900|{tipo_registro}|{quantidade}|\n")
        qtd_linhas_arquivo += 1
        qtd_registros_9900 += 1
        contador_blocos['9'] += 1 
    
    arquivo.write(f'|9900|9999|1|\n')
    arquivo.write(f'|9900|9990|1|\n')
    arquivo.write(f'|9900|9900|{qtd_registros_9900 + 3}|\n')
    arquivo.write(f'|9990|{contador_blocos['9'] + 5}|\n')
    arquivo.write(f'|9999|{qtd_linhas_arquivo + 5}|\n')
    
    contador_registros.clear()
    contador_blocos.clear()
    qtd_linhas_arquivo = 0

def normalizar_cst(cst):
    mapeamento = {
        "00": "000",
        "10": "010",
        "101 ou 102": "102",
        "60": "060",
        "30": "030"
    }
    return mapeamento.get(cst, cst)

def processar_itens(nota, periodo, cnpj, incluir_base_icms=False):
    consolidados = {}
    valor_total_c190 = 0

    for item in nota['itens']:
        # Determinar CFOP e CST
        if nota['indicador_operacao'] == '1':
            cst_icms = item['cst_icms']
            cfop = item['cfop']
        else:
            cst_icms = item['cst_icms']
            cfop = item['cfop']

        cst_icms = normalizar_cst(cst_icms)
        aliq_icms = formata_valor(item['aliq_icms'])
        
        chave = (cst_icms, cfop, aliq_icms)

        if chave not in consolidados:
            consolidados[chave] = {
                'VL_OPR': 0,
                'VL_BC_ICMS': 0 if incluir_base_icms else '0,00',
                'VL_ICMS': 0 if incluir_base_icms else '0,00',
                # 'VL_BC_ICMS_ST': 0 if incluir_base_icms else '0,00',
                # 'VL_ICMS_ST': 0 if incluir_base_icms else '0,00',
                'VL_BC_ICMS_ST': '0,00',
                'VL_ICMS_ST': '0,00',
                'VL_RED_BC': '0,00',
                'VL_IPI': '0,00'
            }

        # Atualiza contador seguro
        chave_contador = f'{cst_icms}_{cfop}'
        contador_csts[periodo][cnpj][chave_contador] = contador_csts[periodo][cnpj].get(chave_contador, 0) + item['valor']

        consolidados[chave]['VL_OPR'] += item['valor']
        valor_total_c190 += item['valor']

        if incluir_base_icms:
            bc_icms = float(str(item['base_calculo_icms']).replace(',', '.'))
            vl_icms = float(str(item['valor_icms']).replace(',', '.'))
            # bc_icms_st = float(str(item['bc_icms_st']).replace(',', '.'))
            # vl_icms_st = float(str(item['valor_icms_st']).replace(',', '.'))
            consolidados[chave]['VL_BC_ICMS'] += bc_icms
            consolidados[chave]['VL_ICMS'] += vl_icms
            # consolidados[chave]['VL_BC_ICMS_ST'] += bc_icms_st
            # consolidados[chave]['VL_ICMS_ST'] += vl_icms_st

    return consolidados, valor_total_c190

def formatar_data(data_iso):
    """
    Converte uma data no formato ISO 8601 (YYYY-MM-DDTHH:MM:SS±HH:MM)
    para o formato DDMMAAAA.
    
    :param data_iso: String da data no formato ISO 8601.
    :return: String da data no formato DDMMAAAA.
    """
    try:
        # Parse da string ISO 8601 para um objeto datetime
        data = datetime.fromisoformat(data_iso)
        # Formatar a data no formato DDMMAAAA
        return data.strftime('%d%m%Y')
    except ValueError:
        raise ValueError(f"Formato de data inválido: {data_iso}")

def formata_valor(valor):
    try:
        valor = float(str(valor).replace(',', '.'))
        return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '')
    except (TypeError, ValueError):
        return "0,00"

@lru_cache()
def get_tipi_df():
    import pandas as pd
    return pd.read_excel('_RECURSOS_/tipi.xlsx')

def buscar_codigo_genero(descricao):
    max_similaridade = 0
    melhor_correspondencia = None
    
    for codigo, descricao_genero in generos.items():
        similaridade = jaccard_similarity(descricao, descricao_genero)
        if similaridade > max_similaridade:
            max_similaridade = similaridade
            melhor_correspondencia = codigo
    if melhor_correspondencia :
        return melhor_correspondencia
    else :
        return ''

def _norm(txt: str) -> str:
    if not txt:
        return ''
    txt = txt.lower()
    # normaliza caracteres mais comuns
    txt = txt.replace('á','a').replace('à','a').replace('ã','a').replace('â','a')
    txt = txt.replace('é','e').replace('ê','e').replace('í','i')
    txt = txt.replace('ó','o').replace('ô','o').replace('õ','o')
    txt = txt.replace('ú','u').replace('ç','c')
    return txt

def _starts_with_any(s: str, prefixes):
    return any(s.startswith(p) for p in prefixes)

def _has_kw(desc_norm: str, kws) -> bool:
    return any(kw in desc_norm for kw in kws)

def determinar_tipo_item(ncm, cfop, descricao):
    """
    Retorna:
      "00" -> Mercadoria para Revenda
      "07" -> Uso/Consumo/Outros (inclui insumo, ativo, energia, frete/servicos)
    Regras (ordem de prioridade):
      1) CFOP específico (ativo, energia, uso/consumo, revenda, insumo)
      2) Palavras-chave da descrição
      3) Heurística por NCM (se você já tem verificar_se_e_comercializado)
      4) Fallback = "07"
    """
    cfop = (cfop or '').strip()
    desc = _norm(descricao or '')
    ncm = (ncm or '').strip()

    # 1) Casos que NUNCA são revenda (classificar como "07")
    if cfop in CFOP_ATIVO_IMOB:
        return "07"  # ativo imobilizado -> não é revenda
    if cfop in CFOP_ENERGIA or _has_kw(desc, KW_ENERGIA):
        return "07"  # energia elétrica -> não é revenda
    if _has_kw(desc, KW_FRETE) or _starts_with_any(cfop, ('1', '2')) and re.fullmatch(r'\d{4}', cfop) and cfop.endswith('53'):
        # Heurística simples p/ CFOP frete tipo x353; ajuste se quiser ser mais estrito.
        return "07"  # frete/serviço (CT-e) -> não é revenda

    # 2) Uso e consumo explícito
    if cfop in CFOP_USO_CONSUMO or _has_kw(desc, KW_USO_CONSUMO):
        return "07"

    # 3) Revenda clara
    if cfop in CFOP_REVENDA or _has_kw(desc, KW_REVENDA):
        return "00"

    # 4) Insumo (produção/prestação)
    if cfop in CFOP_INSUMO or _has_kw(desc, KW_INSUMO):
        return "07"  # no teu M105 atual, você trata "07" como insumo/consumo

    # 5) Heurística por NCM (tua função existente)
    try:
        if verificar_se_e_comercializado(ncm):
            return "00"  # tende a ser mercadoria de revenda
    except Exception:
        # se a função não estiver disponível ou falhar, segue o fluxo
        pass

    # 6) Fallback conservador
    return "07"

def buscar_codigo_ex_tipi(ncm):
    ncm_formatado = f"{ncm[:4]}.{ncm[4:6]}.{ncm[6:]}"
    df = get_tipi_df()
    linha = df[df['NCM'] == ncm_formatado]
    if not linha.empty:
        codigo_ex = linha.iloc[0]['EX']
        return str(codigo_ex) if pd.notnull(codigo_ex) else '0'
    return '0'

def obter_primeiro_e_ultimo_dia(mes_ano: str):
    ano, mes = map(int, mes_ano.split("-"))  # agora lê "2020-09"
    primeiro_dia = datetime(ano, mes, 1)
    ultimo_dia = (primeiro_dia + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    return primeiro_dia.strftime("%d%m%Y"), ultimo_dia.strftime("%d%m%Y")

def converter_sets_para_listas(dado):
    if isinstance(dado, set):
        return list(dado)  # Converte set para lista
    elif isinstance(dado, dict):
        return {chave: converter_sets_para_listas(valor) for chave, valor in dado.items()}
    elif isinstance(dado, list):
        return [converter_sets_para_listas(item) for item in dado]
    return dado

def contar_e_escrever(registro, arquivo):
    global qtd_linhas_arquivo, contador_blocos

    tipo_registro = registro.split('|')[1]
    bloco_registro = tipo_registro[0]
    
    if bloco_registro in contador_blocos :
        contador_blocos[bloco_registro] +=1
    else:
        contador_blocos[bloco_registro] = 1
    
    if tipo_registro in contador_registros :
        contador_registros[tipo_registro] += 1
    else :
        contador_registros[tipo_registro] = 1
        
    arquivo.write(f'{registro}\n')
    qtd_linhas_arquivo += 1 

def gerar_registro_1100(arquivo, dados_cnpj, periodo):

    per_apu_cred = converter_data_para_mes_anterior_mmyyyy(periodo)  # 'YYYY-MM' -> 'MMYYYY'

    saldo_credor_anterior = float(dados_cnpj.get('saldo_credor_anterior_pis', 0) or 0.0)
    saldo_a_transportar   = float(dados_cnpj.get('credito_acumulado_pis', 0) or 0.0)
    
    linha = (
        f"|1100|{per_apu_cred}|01||101|"
        f"{fmt_br(saldo_credor_anterior)}||{fmt_br(saldo_credor_anterior)}|0,00"
        f"|0,00||{fmt_br(saldo_credor_anterior)}"
        f"|{fmt_br(saldo_credor_anterior)}||"
        f"|||0,00|"
    )

    contar_e_escrever(linha, arquivo)
    
def gerar_registro_1500(arquivo, dados_cnpj, periodo):

    per_apu_cred = converter_data_para_mes_anterior_mmyyyy(periodo)  # 'YYYY-MM' -> 'MMYYYY'

    saldo_credor_anterior = float(dados_cnpj.get('saldo_credor_anterior_cofins', 0) or 0.0)
    saldo_a_transportar   = float(dados_cnpj.get('credito_acumulado_cofins', 0) or 0.0)

    linha = (
        f"|1500|{per_apu_cred}|01||101|"
        f"{fmt_br(saldo_credor_anterior)}||{fmt_br(saldo_credor_anterior)}|0,00"
        f"|0,00||{fmt_br(saldo_credor_anterior)}"
        f"|{fmt_br(saldo_credor_anterior)}||"
        f"|||0,00|"
    )

    contar_e_escrever(linha, arquivo)

def gerar_registro_0000(periodo, razao_social, cnpj, inscricao_estadual, uf, cod_municipio, arquivo):
    data_inicial, data_final = obter_primeiro_e_ultimo_dia(periodo)
    ano = data_inicial[-4:]
    layout = '006'
    
    # if ano == '2020':
    #     layout = '014'
    # elif ano == '2021':
    #     layout = '015'
    # elif ano == '2022':
    #     layout = '016'
    # elif ano == '2023':
    #     layout = '017'
    # elif ano == '2024':
    #     layout = '018'
    # elif ano == '2025':
    #     layout = '019'
    
    registro = f"|0000|{layout}|1|||{data_inicial}|{data_final}|{razao_social}|{cnpj}|{uf}|{cod_municipio}||00|9|"
    contar_e_escrever(registro, arquivo)

def gerar_registro_0001(arquivo):
    registro = '|0001|0|'
    contar_e_escrever(registro, arquivo)

def gerar_registro_0100(arquivo):
    registro = registro_0100()  # dados do contabilista vêm do .env (MODULES/config_ambiente.py)
    contar_e_escrever(registro, arquivo)
    
def gerar_registro_0110(arquivo):
    registro = (
        "|0110|1|2|1||")
    contar_e_escrever(registro, arquivo)

def gerar_registro_0111(arquivo, dados_cnpj):
    receita_bruta_tributada_dados_cnpj = dados_cnpj['valor_total_base_01']
    receita_bruta_nao_tributada = ''
    soma_receitas_isentas = 0
    for cst in ['02','03','04','05','06','07','08','09','99']:
        soma_receitas_isentas += float(dados_cnpj[f'valor_total_base_{cst}'])
        
    receita_bruta_total = float(receita_bruta_tributada_dados_cnpj) + soma_receitas_isentas
        
    registro = (f"|0111|{formata_valor(receita_bruta_tributada_dados_cnpj)}|{formata_valor(soma_receitas_isentas)}|0,00|0,00|{formata_valor(receita_bruta_total)}|")
    contar_e_escrever(registro, arquivo)

def gerar_registro_0140(arquivo, razao_social, cnpj, uf, inscricao_estadual, cod_municipio):
    registro = (f"|0140|007|{razao_social}|{cnpj}|{uf}|{inscricao_estadual}|{cod_municipio}|||")
    contar_e_escrever(registro, arquivo)
    
def gerar_registro_0150(destinatarios, arquivo):
    mapa_codigos = {}  # Dicionário para armazenar o mapeamento
    for index, (cnpj_destinatario, dados_destinatario) in enumerate(destinatarios.items(), start=1):
        
        if cnpj_destinatario is None or cnpj_destinatario == "":
            continue  # Pula se o CNPJ/CPF estiver vazio
        
        codigo = f"MPHDEST{index:04}"  # Código único baseado no índice
        razao_social_destinatario = dados_destinatario['razao_social']
        codigo_pais_destinatario = dados_destinatario['codigo_pais']
        inscricao_estadual_destinatario = dados_destinatario['inscricao_estadual']
        codigo_municipio_destinatario = dados_destinatario['codigo_municipio']
        logradouro_destinatario = dados_destinatario['logradouro']
        numero_logradouro_destinatario = dados_destinatario['numero_logradouro']
        bairro_destinatario = dados_destinatario['bairro']
        
        if codigo_pais_destinatario == "" :
            codigo_pais_destinatario = "1058"
        
        if cnpj_destinatario and len(cnpj_destinatario) == 14 :
            registro = f"|0150|{codigo}|{razao_social_destinatario}|{codigo_pais_destinatario}|{cnpj_destinatario}||{inscricao_estadual_destinatario}|{codigo_municipio_destinatario}||{logradouro_destinatario}|{numero_logradouro_destinatario}||{bairro_destinatario}|"
        else :
            registro = f"|0150|{codigo}|{razao_social_destinatario}|{codigo_pais_destinatario}||{cnpj_destinatario}|{inscricao_estadual_destinatario}|{codigo_municipio_destinatario}||{logradouro_destinatario}|{numero_logradouro_destinatario}||{bairro_destinatario}|"

        contar_e_escrever(registro, arquivo)

        # Adiciona o mapeamento CNPJ/CPF -> Código
        mapa_codigos[cnpj_destinatario] = codigo

    return mapa_codigos

def gerar_registro_0190(unidades, arquivo):
    unidades_unicas = []
    
    for unidade in unidades:        
        unidade = unidade.upper().replace(' ', '')
        if unidade not in unidades_unicas :
            unidades_unicas.append(unidade)
            registro = f'|0190|{unidade}|Unidade Importada Nfe|'
            contar_e_escrever(registro, arquivo)

def gerar_registro_0200(itens, arquivo):
    itens_unicos = {}

    for index, item in enumerate(itens, start=1):
        # Gera um identificador único (por exemplo, com NCM + Nome)
        identificador = f"{item['ncm']}-{item['nome_item_nota']}"
        codigo = f"MPHPROD{index:04}"

        if identificador not in itens_unicos:
            
            tipo_item = determinar_tipo_item(item['ncm'], item['cfop'], item['nome_item_nota'])
            
            if item['ncm'] == '00':
                tipo_item = '09'
            
            codigo_ex = buscar_codigo_ex_tipi(item['ncm'])
            codigo_genero = buscar_codigo_genero(item['nome_item_nota'])

            # Adiciona o item ao dicionário de itens únicos
            itens_unicos[identificador] = codigo
                        
            # Formata o registro 0200
            registro = f"|0200|{codigo}|{item['nome_item_nota'].replace('|','')}|{item['codigo_barras']}||{item['unidade'].upper().replace(' ', '')}|{tipo_item}|{item['ncm']}|{codigo_ex}|{codigo_genero}||{formata_valor(item['aliq_icms'])}|"

            # Escreve o registro no arquivo
            contar_e_escrever(registro, arquivo)

    return itens_unicos

def gerar_registro_0400(naturezas, arquivo):
    naturezas_unicas = {}
    
    for index, natureza in enumerate(naturezas) :
        natureza = natureza.lower()
        
        if natureza not in naturezas_unicas:
            codigo = f"MPHNAT{index:04}"
            
            naturezas_unicas[natureza] = codigo

            registro = f"|0400|{codigo}|{natureza}|"
            
            contar_e_escrever(registro, arquivo)
    
    return naturezas_unicas

def gerar_registro_0450(informacoes, arquivo):
    mapa_codigos = {}
    
    for index, informacao in enumerate(informacoes) :
        if informacao not in mapa_codigos:
            codigo = f"MPHIFC{index:04}"
            
            mapa_codigos[informacao] = codigo
            
            registro = f"|0450|{codigo}|{informacao}|"
            
            contar_e_escrever(registro, arquivo)
    
    return mapa_codigos

def gerar_registro_0500(arquivo):
    contar_e_escrever('|0500|01012000|01|A|5|55|ESTOQUE DE MERCADORIA|1.01.03.01.01||', arquivo)
    contar_e_escrever('|0500|01012000|04|S|4|2398|RECEITA BRUTA DE VENDAS DE MERCADORIAS|3.01.01.01.01||', arquivo)
    contar_e_escrever('|0500|01012000|04|A|5|2399|RECEITA DE VENDA DE MERCADORIAS|3.01.01.01.01.02||', arquivo)
    contar_e_escrever('|0500|01012000|04|A|5|2429|MATERIAL DE USO E CONSUMO|3.11.01.09.01.99||', arquivo)

def gerar_registro_0900(arquivo, dados_cnpj):
    
    registro = (
        f'|0900|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|'
    )
    
    contar_e_escrever(registro, arquivo)

def gerar_bloco_a(arquivo):
    contar_e_escrever('|A001|1|', arquivo)
    contar_e_escrever('|A990|2|', arquivo)

def gerar_bloco_c(arquivo, cnpj):
    contar_e_escrever('|C001|0|', arquivo)
    contar_e_escrever(f'|C010|{cnpj}|2|', arquivo)

def gerar_registro_c100(notas_saida, mapa_codigos, arquivo, periodo, cnpj, mapa_codigos_itens, mapa_codigos_naturezas):
    for nota in notas_saida:
        cnpj_destinatario = nota['cnpj_destinatario']
        codigo_participante = mapa_codigos.get(cnpj_destinatario, "")
        data_formatada = formatar_data(nota['data_emissao'])
        if nota['indicador_operacao'] == '1':
            if nota['modelo'] == '65' :
                codigo_participante = ''
                
                soma_total_itens = sum(float(item['valor']) for item in nota['itens'])
                total_nota = float(nota['valor_total'])
                valor_mercadorias = float(nota['valor_mercadorias'])

                if valor_mercadorias > total_nota:
                    ...
                elif total_nota > valor_mercadorias:
                    nota['valor_mercadorias'] = total_nota
            
            soma_total_itens = sum(float(item['valor']) for item in nota['itens'])
            total_nota = float(nota['valor_total'])
            valor_mercadorias = float(nota['valor_mercadorias'])

            if valor_mercadorias > soma_total_itens:
                ...
            elif soma_total_itens > valor_mercadorias:
                nota['valor_mercadorias'] = soma_total_itens
                            
            registro = (
                f"|C100|1|0|{codigo_participante}|{nota['modelo']}|00|{nota['serie']}|{nota['numero']}|{nota['chave']}|"
                f"{data_formatada}|{data_formatada}|"
                f"{str(nota['valor_total']).replace('.', ',')}|{nota['tipo_pagamento']}|"
                f"{str(nota['valor_desconto']).replace('.', ',')}|0,00|{formata_valor(soma_total_itens)}|{nota['tipo_frete']}|"
                f"{str(nota['valor_frete']).replace('.', ',')}|{str(nota['valor_seguro']).replace('.', ',')}|"
                f"{str(nota['valor_outros']).replace('.', ',')}|{str(nota['valor_bc_icms']).replace('.', ',')}|"
                f"{str(nota['valor_icms']).replace('.', ',')}|{str(nota['valor_bc_icms_st']).replace('.', ',')}|{str(nota['valor_icms_st']).replace('.', ',')}||{str(nota['valor_pis']).replace('.', ',')}|{str(nota['valor_cofins']).replace('.', ',')}|||"
            )
            
            contar_e_escrever(registro, arquivo)
            
            if nota['modelo'] == '65' :
                gerar_registro_c175(nota, arquivo)
            else:
                gerar_registro_c170(nota, mapa_codigos_itens, mapa_codigos_naturezas, arquivo)

        if nota['indicador_operacao'] == '0':
            cnpj_emitente = nota['cnpj_emitente']
            codigo_participante = mapa_codigos.get(cnpj_emitente, "")
            data_formatada = formatar_data(nota['data_emissao'])
            
            soma_total_itens = sum(float(item['valor_unitario']) for item in nota['itens'])
            total_nota = float(nota['valor_total'])

            if soma_total_itens > total_nota:
                nota['valor_mercadorias'] = soma_total_itens 
            else :
                nota['valor_mercadorias'] = total_nota 
            
            nota['valor_pis'] = sum (
                float(item['valor_pis'].replace(',','.')) for item in nota['itens']
            )
            
            nota['valor_cofins'] = sum (
                float(item['valor_cofins'].replace(',','.')) for item in nota['itens']
            )
                
            registro = (
                f"|C100|0|{nota['indicador_emissao']}|{codigo_participante}|{nota['modelo']}|00|{nota['serie']}|{nota['numero']}|{nota['chave']}|"
                f"{data_formatada}|{data_formatada}|"
                f"{str(nota['valor_total']).replace('.', ',')}|{nota['tipo_pagamento']}|"
                f"{str(nota['valor_desconto']).replace('.', ',')}|0,00|{formata_valor(nota['valor_mercadorias'])}|{nota['tipo_frete']}|"
                f"{str(nota['valor_frete']).replace('.', ',')}|{str(nota['valor_seguro']).replace('.', ',')}|"
                f"{str(nota['valor_outros']).replace('.', ',')}|{str(nota['valor_bc_icms']).replace('.', ',')}|"
                f"{str(nota['valor_icms']).replace('.', ',')}|{str(nota['valor_bc_icms_st']).replace('.', ',')}|{str(nota['valor_icms_st']).replace('.', ',')}||{formata_valor(nota['valor_pis'])}|{formata_valor(nota['valor_cofins'])}|||"
            )
            
            contar_e_escrever(registro, arquivo)
            
            gerar_registro_c170(nota, mapa_codigos_itens, mapa_codigos_naturezas, arquivo)

def gerar_registro_c175(nota, arquivo):
    if nota["modelo"] != "65":
        return  # só NFC-e
    
    consolidados = {}
    for item in nota["itens"]:
        chave = (item["cfop"], item["cst_pis_correto"], normaliza_aliquota(item["aliquota_pis_correto"]), 
                 item["cst_cofins_correto"], normaliza_aliquota(item["aliquota_cofins_correto"]))
        
        if chave not in consolidados:
            consolidados[chave] = {
                "VL_OPR": 0.0, "VL_DESC": 0.0,
                "VL_BC_PIS": 0.0, "VL_PIS": 0.0,
                "VL_BC_COFINS": 0.0, "VL_COFINS": 0.0
            }
        
        consolidados[chave]["VL_OPR"] += float(item["valor"])
        consolidados[chave]["VL_BC_PIS"] += round(float(item["base_calculo_pis_correto"]), 2)
        consolidados[chave]["VL_PIS"] += float(item["valor_pis_correto"])
        consolidados[chave]["VL_BC_COFINS"] += round(float(item["base_calculo_cofins_correto"]), 2)
        consolidados[chave]["VL_COFINS"] += float(item["valor_cofins_correto"])
    
    for (cfop, cst_pis, aliq_pis, cst_cofins, aliq_cofins), v in consolidados.items():
                
        registro = (
            f"|C175|{cfop}|{v['VL_OPR']:.2f}|{v['VL_DESC']:.2f}|"
            f"{cst_pis}|{v['VL_BC_PIS']:.2f}|{formata_valor(normaliza_aliquota(float(aliq_pis)))}|||{v['VL_PIS']:.2f}|"
            f"{cst_cofins}|{v['VL_BC_COFINS']:.2f}|{formata_valor(normaliza_aliquota(float(aliq_cofins)))}|||{v['VL_COFINS']:.2f}|2399||"
        ).replace(".", ",")
        
        contar_e_escrever(registro, arquivo)
        
def gerar_registro_c170(nota, mapa_codigos_items, mapa_codigos_naturezas, arquivo):    
    codigo_natureza = ''

    for item in nota['itens']:
        identificador = f"{item['ncm']}-{item['nome_item_nota']}"
        codigo_item = mapa_codigos_items.get(identificador, "FUDEU")
        
        if len(item['cst_icms']) == 2 :
            item['cst_icms'] = item['origem_icms'] + item['cst_icms']
        elif len(item['cst_icms']) == 3 :
            item['cst_icms'] = item['cst_icms']
            
        cfop = item['cfop']    
        item['cst_cofins_saida'] = item['cst_cofins']
        item['cst_pis_saida'] = item['cst_pis']
        
        # if nota['indicador_operacao'] == '0':
            # if cfop[0] == "5":
            #     cfop = "1" + cfop[1:]
            # elif cfop[0] == "6":
            #     cfop = "2" + cfop[1:]
            # elif cfop[0] == "7":
            #     cfop = "3" + cfop[1:]
            
            # if cfop == "1405":
            #     cfop = "1403"
            
            # if cfop == "2929":
            #     cfop = "2653"
            
            # if cfop == "1667" or cfop == "1656":
            #     cfop = "1653"
                
            # if cfop == "1929":
            #     cfop = "1556"
            
            # if cfop == '2106':
            #     cfop = '1101'
                
            # if cfop == '1949':
            #     cfop = '1128'
                
            # if cfop == '1402':
            #     cfop = '1556'
            
            # if cfop == '2108':
            #     cfop = '2556'
            
            # if cfop == '2667':
            #     cfop = '2653'
                
            # if cfop == '2656':
            #     cfop = '2653'
            
            # if cfop == '1655':
            #     cfop = '2662'
            
            # if cfop == '1915' or cfop == '1909':
            #     cfop = '1102'
            
            # if cfop == '1110':
            #     cfop = '1101'
            
            # if item['cst_pis'] == '01':
            #     item['cst_pis_saida'] = '50'
            #     item['cst_cofins_saida'] = '50'
                
            # elif item['cst_pis'] == '02':
            #     item['cst_pis_saida'] = '50'
            #     item['cst_cofins_saida'] = '50'
                
            # elif item['cst_pis'] == '03':
            #     item['cst_pis_saida'] = '50'
            #     item['cst_cofins_saida'] = '50'
                
            # elif item['cst_pis'] == '04':
            #     item['cst_pis_saida'] = '70'
            #     item['cst_cofins_saida'] = '70'
                
            # elif item['cst_pis'] == '05':
            #     item['cst_pis_saida'] = '75'
            #     item['cst_cofins_saida'] = '75'
                
            # elif item['cst_pis'] == '06':
            #     item['cst_pis_saida'] = '73'
            #     item['cst_cofins_saida'] = '73'
                
            # elif item['cst_pis'] == '07':
            #     item['cst_pis_saida'] = '71'
            #     item['cst_cofins_saida'] = '71'
                
            # elif item['cst_pis'] == '08':
            #     item['cst_pis_saida'] = '74'
            #     item['cst_cofins_saida'] = '74'
                
            # elif item['cst_pis'] == '09':
            #     item['cst_pis_saida'] = '72'
            #     item['cst_cofins_saida'] = '72'
                
            # elif item['cst_pis'] == '49':
            #     item['cst_pis_saida'] = '99'
            #     item['cst_cofins_saida'] = '99'
            
            # item['cfop'] = cfop
            # item['cst_pis'] = item['cst_pis_saida']
            # item['cst_cofins'] = item['cst_cofins_saida']
            # item['cst_pis_correto'] = item['cst_pis_saida']
            # item['cst_cofins_correto'] = item['cst_cofins_saida']
            # item['base_calculo_pis_correto'] = item['base_calculo_pis']
            # item['base_calculo_cofins_correto'] = item['base_calculo_cofins']
            # item['aliquota_pis_correto'] = item['aliq_pis']
            # item['aliquota_cofins_correto'] = item['aliq_cofins']
            # item['valor_pis_correto'] = item['valor_pis']
            # item['valor_cofins_correto'] = item['valor_cofins']
            
        
        if item['base_calculo_pis_correto'] != '0,00':
            item['base_calculo_pis_correto'] = round(float(item['base_calculo_pis_correto']),2)
        
        if item['base_calculo_cofins_correto'] != '0,00':
            item['base_calculo_cofins_correto'] = round(float(item['base_calculo_cofins_correto']),2)
            
        registro = (
            f"|C170|{item['numero_item']}|{codigo_item}|{item['nome_item_nota'].replace('|','')}|"
            f"{formata_valor(item['quantidade_item'])}|{item['unidade'].upper().replace(' ', '')}|{formata_valor(item['valor'])}|"
            f"{formata_valor(item['desconto_item_nota'])}|1|{item['cst_icms']}|{cfop}|{codigo_natureza}|"
            f"{formata_valor(item['base_calculo_icms'])}|{formata_valor(item['aliq_icms'])}|{formata_valor(item['valor_icms'])}|{formata_valor(item['bc_icms_st'])}|{formata_valor(item['aliq_icms_st'])}|{formata_valor(item['valor_icms_st'])}|0|"
            f"||0,00|{formata_valor(item['aliq_ipi'])}|{formata_valor(item['valor_ipi'])}|"
            f"{item['cst_pis_correto']}|{formata_valor(item['base_calculo_pis_correto'])}|{formata_valor(normaliza_aliquota(item['aliquota_pis_correto']))}|||{formata_valor(item['valor_pis_correto'])}|{item['cst_cofins_correto']}|{formata_valor(item['base_calculo_cofins_correto'])}|{formata_valor(normaliza_aliquota(item['aliquota_cofins_correto']))}|||{formata_valor(item['valor_cofins_correto'])}|2399|"
        )        

        contar_e_escrever(registro, arquivo)

def gerar_registro_c190(nota, arquivo, periodo, cnpj):
    valor_total_nota = nota['valor_total']

    if nota['indicador_operacao'] not in ['0', '1']:
        return  # ignora notas com indicador inválido

    incluir_base_icms = nota['indicador_operacao'] == '0'
    consolidados, valor_total_c190 = processar_itens(nota, periodo, cnpj, incluir_base_icms)

    diferenca = float(valor_total_nota) - float(valor_total_c190)

    registros = list(consolidados.items())
    if registros and diferenca > 0:
        ultima_chave, ultimos_valores = registros[-1]
        ultimos_valores['VL_OPR'] += diferenca
        registros[-1] = (ultima_chave, ultimos_valores)

    for (cst_icms, cfop, aliq_icms), valores in registros:
        registro = (
            f"|C190|{cst_icms}|{cfop}|{aliq_icms}|"
            f"{str(round(valores['VL_OPR'], 2)).replace('.', ',')}|"
        )

        if incluir_base_icms:
            registro += (
                f"{str(round(valores['VL_BC_ICMS'], 2)).replace('.', ',')}|"
                f"{str(round(valores['VL_ICMS'], 2)).replace('.', ',')}|"
                # f"{str(round(valores['VL_BC_ICMS_ST'], 2)).replace('.', ',')}|"
                # f"{str(round(valores['VL_ICMS_ST'], 2)).replace('.', ',')}|"
            )
        else:
            registro += (f"{valores['VL_BC_ICMS']}|{valores['VL_ICMS']}|"
                        # f"{valores['VL_BC_ICMS_ST']}|{valores['VL_ICMS_ST']}|"
            )

        registro += (
            f"{valores['VL_BC_ICMS_ST']}|{valores['VL_ICMS_ST']}|"
            f"{valores['VL_RED_BC']}|{valores['VL_IPI']}||"
        )
        contar_e_escrever(registro, arquivo)

def gerar_registro_d001(arquivo):
    contar_e_escrever('|D001|0|', arquivo)

def gerar_registro_d010(arquivo, dados_cnpj, cnpj):
    
    contar_e_escrever(f'|D010|{cnpj}|', arquivo) 

def gerar_registro_d100(arquivo, dados_cnpj, mapa_codigos_participantes):
    for cte in dados_cnpj['entradas_cte']:
        
        cnpj_destinatario = cte['cnpj_destinatario']
        codigo_participante = mapa_codigos_participantes.get(cnpj_destinatario, "")
        modelo_cte = cte['modelo']
        serie = cte['modelo']
        numero = cte['numero_cte']
        chave_nota = cte['chave_nota']
        data_emissao = cte['data_emissao'].replace('/','')
        data_recebimento = cte['data_recebimento'].replace('/','')
        tipo_cte = cte['tipo_cte']
        valor_nota = formata_valor(cte['valor_nota'])
        indicador_frete = cte['indicador_frete']
        base_icms = formata_valor(cte['base_icms'])
        valor_icms = formata_valor(cte['valor_icms'])
        
        valor_nota = str(valor_nota).replace(',','.')
        
        valor_pis = float(valor_nota) * (float(ALIQ_PIS.replace(',','.')) / 100)
        cte['valor_pis'] = formata_valor(valor_pis)
        valor_cofins = float(valor_nota) * (float(ALIQ_COFINS.replace(',','.')) / 100)
        cte['valor_cofins'] = formata_valor(valor_cofins)
                
        contar_e_escrever(f'|D100|0|1|{codigo_participante}|{modelo_cte}|00|{serie}||{numero}|{chave_nota}|{data_emissao}|{data_recebimento}|{tipo_cte}||{formata_valor(valor_nota)}|0|{indicador_frete}|{formata_valor(valor_nota)}|{base_icms}|{valor_icms}|||2399|', arquivo)
        
        gerar_registro_d101(arquivo, dados_cnpj, cte)
        gerar_registro_d105(arquivo, dados_cnpj, cte)
        
def gerar_registro_d101(arquivo, dados_cnpj, cte):
    
    if cte['indicador_toma'] != '3':
        return
    
    registro = (f"|D101|2|{formata_valor(cte['valor_nota'])}|50|01|{formata_valor(cte['valor_nota'])}|1,65|{formata_valor(cte['valor_pis'])}|2399|")
    contar_e_escrever(registro, arquivo)
    
def gerar_registro_d105(arquivo, dados_cnpj, cte):
    
    if cte['indicador_toma'] != '3':
        return
    
    registro = (f"|D105|2|{formata_valor(cte['valor_nota'])}|50|01|{formata_valor(cte['valor_nota'])}|7,60|{formata_valor(cte['valor_cofins'])}|2399|")
    contar_e_escrever(registro, arquivo)
    
def gerar_registro_f001(arquivo):
    contar_e_escrever('|F001|1|', arquivo)
    
def gerar_registro_f010(arquivo, cnpj):
    contar_e_escrever(f'|F010|{cnpj}|', arquivo)

def gerar_registro_f100(arquivo):
    ...

def gerar_registro_i001(arquivo):
    contar_e_escrever('|I001|1|', arquivo)

def gerar_registro_m001(arquivo):
    contar_e_escrever('|M001|0|', arquivo)

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

def gerar_registro_m100(arquivo, dados_cnpj):
    # id_credito_total_parcial = '0'
    """
    Gera os registros M100 apenas a partir dos dados já apurados em
    calcular_credito_mes_pis_cofins / apurar_pis_cofins.

    Requer que dados_cnpj contenha as chaves:
        'base_credito_pis_no_mes'         -> dict { "CST_aliq" : base }
        'credito_pis_por_chave_no_mes'    -> dict { "CST_aliq" : { ... } }
    """
    
    base_credito_pis   = dados_cnpj.get('base_credito_pis_no_mes') or {}
    creditos_por_chave = dados_cnpj.get('credito_pis_por_chave_no_mes') or {}


    for chave, base in base_credito_pis.items():
        # chave no formato "CST_aliquota"
        try:
            cst, aliquota_norm = chave.split('_', 1)
        except ValueError:
            print(f'Chave de base de crédito inválida: {chave}')
            continue

        codigos = codigo_credito_por_aliquota(cst, aliquota_norm)
        if not codigos:
            # print(f'AVISO: CST {cst} não mapeado para códigos de crédito. Pulando...')
            continue
        cod_credito = codigos[0]

        info_credito = creditos_por_chave.get(chave, 0.0)

        credito_original = formata_valor(info_credito['credito_original'])
        credito_descontado = formata_valor(info_credito['credito_descontado'])
        saldo_credor = formata_valor(info_credito['valor_abatido'])

        base_num = float(base)
        
        if info_credito['valor_abatido'] > 0.1 :
            print(f'Atenção: Crédito PIS/COFINS utilizado no mês para CST {cst} alíquota {aliquota_norm}: {formata_valor(info_credito["valor_abatido"])}')
            id_credito_total_parcial = '1'
        else:
            id_credito_total_parcial = '0'
            
        contar_e_escrever(
            f'|M100|{cod_credito}|0|{formata_valor(base_num)}|{formata_valor(aliquota_norm)}|||'
            f'{credito_original}|0,00|0,00|0,00|{credito_original}|{id_credito_total_parcial}|'
            f'{credito_descontado}|{saldo_credor}|',
            arquivo
        )

        gerar_registro_m105(arquivo, dados_cnpj, cst, aliquota_norm, cod_credito)

def gerar_registro_m105(arquivo, dados_cnpj, cst, aliquota, codigo_credito):
    aliq_norm_ref = normaliza_aliquota(aliquota)

    base_total_revenda = 0
    base_total_consumo = 0
    base_aquisicao_transporte = 0
    base_total_servicos = 0
    base_total_devolucao = 0
    base_sem_credito = 0

    # 1) Notas de entrada
    for nota in dados_cnpj.get('notas', []):
        if str(nota.get('indicador_operacao', '0')) != '0':
            continue
        for item in nota.get('itens', []) or []:
            cst_pis = str(item.get('cst_pis', '')).zfill(2)
            aliq_item_norm = normaliza_aliquota(item.get('aliq_pis', 0))
            base_pis = float(item['base_calculo_pis'].replace(',','.'))
            if cst_pis == cst and aliq_item_norm == aliq_norm_ref:
                cod_nat = determinar_cod_nat_base_credito(item)
                if cod_nat == '01':
                    base_total_revenda += base_pis
                elif cod_nat == '02':
                    base_total_consumo += base_pis
                elif cod_nat == '03':
                    base_total_servicos += base_pis
                elif cod_nat == '12':
                    base_total_devolucao += base_pis
                elif cod_nat == '13':
                    base_sem_credito += base_pis
                elif cod_nat == '14':
                    base_aquisicao_transporte += base_pis
    
    if cst == '50' and aliq_norm_ref == '1.65':
        base_total_revenda += float(dados_cnpj['credito_por_entradas_cte_pis_cofins'])
    
    if base_total_revenda > 0:    
        contar_e_escrever(
            f'|M105|01|{cst}|{formata_valor(base_total_revenda)}|0,00|{formata_valor(base_total_revenda)}|{formata_valor(base_total_revenda)}|||CREDITO REFERENTE A COMPRA DE MERCADORIAS PARA REVENDA|',
            arquivo
        )
    if base_total_consumo > 0:
        contar_e_escrever(
            f'|M105|02|{cst}|{formata_valor(base_total_consumo)}|0,00|{formata_valor(base_total_consumo)}|{formata_valor(base_total_consumo)}|||CREDITO REFERENTE A COMPRA DE BENS PARA USO/CONSUMO|',
            arquivo
        )
    
    if base_sem_credito > 0:
        contar_e_escrever(
            f'|M105|13|{cst}|{formata_valor(base_sem_credito)}|0,00|{formata_valor(base_sem_credito)}|{formata_valor(base_sem_credito)}|||BASE DE CALCULO SEM DIREITO A CREDITO|',
            arquivo
        )
    
    if base_total_servicos > 0:
        contar_e_escrever(
            f'|M105|03|{cst}|{formata_valor(base_total_servicos)}|0,00|{formata_valor(base_total_servicos)}|{formata_valor(base_total_servicos)}|||CREDITO REFERENTE A AQUISICAO DE SERVICOS|',
            arquivo
        )
        
    if base_total_devolucao > 0:
        contar_e_escrever(
            f'|M105|12|{cst}|{formata_valor(base_total_devolucao)}|0,00|{formata_valor(base_total_devolucao)}|{formata_valor(base_total_devolucao)}|||DEVOLUCAO DE MERCADORIAS RECEBIDAS COM DIREITO A CREDITO|',
            arquivo
        )
    
    if base_aquisicao_transporte > 0:
        contar_e_escrever(
            f'|M105|14|{cst}|{formata_valor(base_aquisicao_transporte)}|0,00|{formata_valor(base_aquisicao_transporte)}|{formata_valor(base_aquisicao_transporte)}|||AQUISICAO DE SERVICOS DE TRANSPORTE|',
            arquivo
        )
 
def gerar_registro_m200(arquivo, dados_cnpj):

    credito_pis_do_mes    = str(round(float(dados_cnpj.get('credito_descontado_total_pis', 0)), 2)).replace(',','').replace('.', ',')
    saldo_credor_anterior = fmt_br(dados_cnpj.get('saldo_credor_anterior_pis', 0))
    debito_pis_do_mes     = fmt_br(dados_cnpj.get('debito_pis_do_mes', 0))
    debito_a_pagar_pis    = formata_valor(dados_cnpj.get('debito_a_pagar_pis', 0))

    # regra de espelhamento quando há crédito acumulado
    # if dados_cnpj.get('credito_acumulado_pis', 0) > 0:
    #     credito_pis_do_mes = debito_pis_do_mes

    linha = (
        f"|M200|{debito_pis_do_mes}|{credito_pis_do_mes}|{saldo_credor_anterior}|"
        f"{debito_a_pagar_pis}|0,00|0,00|{debito_a_pagar_pis}|0,00|0,00|0,00|0,00|{debito_a_pagar_pis}|"
    )
    contar_e_escrever(linha, arquivo)

def gerar_registro_m205(arquivo, dados_cnpj):
    if float(dados_cnpj['debito_a_pagar_pis']) <= 0:
        return
    
    debito_a_pagar_pis = formata_valor(dados_cnpj['debito_a_pagar_pis'])
    
    contar_e_escrever(f'|M205|08|691201|{debito_a_pagar_pis}|', arquivo)
    
def gerar_registro_m210(arquivo, dados_cnpj):
    contar_e_escrever(
        f"|M210|01|{formata_valor(dados_cnpj['valor_total_base_01'])}|{formata_valor(dados_cnpj['base_original_pis_cofins'])}|0,00|{formata_valor(dados_cnpj['credito_pis_cofins_icms_st'])}|"
        f"{formata_valor(dados_cnpj['base_pis_cofins_sem_icms_st'])}|1,6500|||{formata_valor(dados_cnpj['debito_pis_do_mes'])}|0,00|0,00|0,00|0,00|"
        f"{formata_valor(dados_cnpj['debito_pis_do_mes'])}|",
        arquivo
    )

def gerar_registro_m215(arquivo, dados_cnpj, cnpj, periodo):
    registro = (
        f"|M215|0|{formata_valor(dados_cnpj['credito_pis_cofins_icms_st'])}|42||Exclusão do valor do ICMS-ST destacado nas notas fiscais de entrada conforme Solução COSIT nº 100/2025.|{ultimo_dia_mes(periodo)}|2399|{cnpj}||"
    )
    
    contar_e_escrever(registro, arquivo)

def gerar_registro_m400(arquivo, dados_cnpj):
    base_04 = dados_cnpj['valor_total_base_04']
    base_05 = dados_cnpj['valor_total_base_05']
    base_06 = dados_cnpj['valor_total_base_06']
    base_07 = dados_cnpj['valor_total_base_07']
    base_08 = dados_cnpj['valor_total_base_08']
    base_09 = dados_cnpj['valor_total_base_09']

    # === 4) Escrita dos registros M400 ===
    if base_04 > 0:
        contar_e_escrever(
            f"|M400|04|{formata_valor(base_04)}|2398||", arquivo
        )
    
    if base_05 > 0:
        contar_e_escrever(
            f"|M400|05|{formata_valor(base_05)}|2398||", arquivo
        )
    
    if base_06 > 0:
        contar_e_escrever(
            f"|M400|06|{formata_valor(base_06)}|2398||", arquivo
        )
    
    if base_07 > 0:
        contar_e_escrever(
            f"|M400|07|{formata_valor(base_07)}|2398||", arquivo
        )
        
    if base_08 > 0:
        contar_e_escrever(
            f"|M400|08|{formata_valor(base_08)}|2398||", arquivo
        )
    
    if base_09 > 0:
        contar_e_escrever(
            f"|M400|09|{formata_valor(base_09)}|2398||", arquivo
        )

def gerar_registro_m410(arquivo, dados_cnpj):
    contar_e_escrever(f'|M410|102|{formata_valor(dados_cnpj["valor_total_base_06"])}|2399||', arquivo)

def gerar_registro_m500(arquivo, dados_cnpj):
    """
    Gera os registros M500 apenas a partir dos dados já apurados em
    calcular_credito_mes_pis_cofins / apurar_pis_cofins.

    Requer que dados_cnpj contenha as chaves:
        'base_credito_cofins_no_mes'      -> dict { "CST_aliq" : base }
        'credito_cofins_por_chave_no_mes' -> dict { "CST_aliq" : { ... } }
    """
    base_credito_cofins = dados_cnpj.get('base_credito_cofins_no_mes') or {}
    creditos_por_chave  = dados_cnpj.get('credito_cofins_por_chave_no_mes') or {}

    for chave, base in base_credito_cofins.items():
        # chave no formato "CST_aliquota"
        try:
            cst, aliquota_norm = chave.split('_', 1)
        except ValueError:
            print(f'Chave de base de crédito COFINS inválida: {chave}')
            continue

        codigos = codigo_credito_por_aliquota(cst, aliquota_norm)
        if not codigos:
            # print(f'AVISO: CST {cst} não mapeado para códigos de crédito (COFINS). Pulando...')
            continue
        cod_credito = codigos[0]

        info_credito = creditos_por_chave.get(chave, 0.0)

        credito_original   = formata_valor(info_credito.get('credito_original', 0.0))
        credito_descontado = formata_valor(info_credito.get('credito_descontado', 0.0))
        saldo_credor       = formata_valor(info_credito.get('valor_abatido', 0.0))

        base_num = float(base)
        
        if info_credito['valor_abatido'] > 0.1 :
            print(f'Atenção: Crédito PIS/COFINS utilizado no mês para CST {cst} alíquota {aliquota_norm}: {formata_valor(info_credito["valor_abatido"])}')
            id_credito_total_parcial = '1'
        else:
            id_credito_total_parcial = '0'

        contar_e_escrever(
            f'|M500|{cod_credito}|0|{formata_valor(base_num)}|{formata_valor(aliquota_norm)}|||'
            f'{credito_original}|0,00|0,00|0,00|{credito_original}|{id_credito_total_parcial}|'
            f'{credito_descontado}|{saldo_credor}|',
            arquivo
        )

        # Usa o mesmo CST/alíquota no M505
        gerar_registro_m505(arquivo, dados_cnpj, cst, aliquota_norm, cod_credito)
        
def gerar_registro_m505(arquivo, dados_cnpj, cst, aliquota, codigo_credito):
    
    aliq_norm_ref = normaliza_aliquota(aliquota)

    base_total_revenda = 0
    base_total_consumo = 0
    base_aquisicao_transporte = 0
    base_total_servicos = 0
    base_total_devolucao = 0
    base_sem_credito = 0
    
    for nota in dados_cnpj.get('notas', []):
        if nota['indicador_operacao'] != '0':  # apenas entradas
            continue

        for item in nota.get('itens', []) or []:
            cst_cofins = str(item.get('cst_cofins', '')).zfill(2)
            aliq_item_norm = normaliza_aliquota(item.get('aliq_cofins', 0))
            base_cofins = float(item['base_calculo_cofins'].replace(',','.'))

            if cst_cofins == cst and aliq_item_norm == aliq_norm_ref:
                cod_nat = determinar_cod_nat_base_credito(item)
                
                if cod_nat == '01':
                    base_total_revenda += base_cofins
             
                elif cod_nat == '02':
                    base_total_consumo += base_cofins
                    
                elif cod_nat == '03':
                    base_total_servicos += base_cofins
                
                elif cod_nat == '12':
                    base_total_devolucao += base_cofins
                    
                elif cod_nat == '13':
                    base_sem_credito += base_cofins
                
                elif cod_nat == '14':
                    base_aquisicao_transporte += base_cofins
                    
                else :
                    print('codigo natureza nao mapeado', cod_nat)
                    
    if cst == '50' and aliq_norm_ref == '7.60':
        base_total_revenda += float(dados_cnpj['credito_por_entradas_cte_pis_cofins'])
    
    if base_total_revenda > 0:
        contar_e_escrever(
            f'|M505|01|{cst}|{formata_valor(base_total_revenda)}|0,00|{formata_valor(base_total_revenda)}|{formata_valor(base_total_revenda)}|||CREDITO REFERENTE A COMPRA DE MERCADORIAS PARA REVENDA|',
            arquivo
        )            

    if base_total_consumo > 0 :
        contar_e_escrever(
            f'|M505|02|{cst}|{formata_valor(base_total_consumo)}|0,00|{formata_valor(base_total_consumo)}|{formata_valor(base_total_consumo)}|||CREDITO REFERENTE A COMPRA DE BENS PARA USO/CONSUMO|',
            arquivo
        )
        
    if base_sem_credito > 0 :
        contar_e_escrever(
            f'|M505|13|{cst}|{formata_valor(base_sem_credito)}|0,00|{formata_valor(base_sem_credito)}|{formata_valor(base_sem_credito)}|||BASE DE CALCULO SEM DIREITO A CREDITO|',
            arquivo
        )
    
    if base_total_devolucao > 0:
        contar_e_escrever(
            f'|M505|12|{cst}|{formata_valor(base_total_devolucao)}|0,00|{formata_valor(base_total_devolucao)}|{formata_valor(base_total_devolucao)}|||DEVOLUCAO DE MERCADORIAS RECEBIDAS COM DIREITO A CREDITO|',
            arquivo
        )
    
    if base_total_servicos > 0 :
        contar_e_escrever(
            f'|M505|03|{cst}|{formata_valor(base_total_servicos)}|0,00|{formata_valor(base_total_servicos)}|{formata_valor(base_total_servicos)}|||CREDITO REFERENTE A AQUISICAO DE SERVICOS EM GERAL|',
            arquivo
        )
    
    if base_aquisicao_transporte > 0 :
        contar_e_escrever(
            f'|M505|14|{cst}|{formata_valor(base_aquisicao_transporte)}|0,00|{formata_valor(base_aquisicao_transporte)}|{formata_valor(base_aquisicao_transporte)}|||AQUISICAO DE SERVICOS DE TRANSPORTE|',
            arquivo
        )    
    
def gerar_registro_m600(arquivo, dados_cnpj):

    credito_cofins_do_mes = formata_valor(dados_cnpj.get('credito_descontado_total_cofins', 0))
    saldo_credor_anterior = formata_valor(dados_cnpj.get('saldo_credor_anterior_cofins', 0))
    debito_cofins_do_mes = formata_valor(dados_cnpj.get('debito_cofins_do_mes', 0))
    debito_a_pagar_cofins = formata_valor(dados_cnpj['debito_a_pagar_cofins'])

    # if dados_cnpj['credito_acumulado_cofins'] > 0:
    #     credito_cofins_do_mes = debito_cofins_do_mes
    
    linha = (
        f"|M600|{formata_valor(debito_cofins_do_mes)}|{credito_cofins_do_mes}|{saldo_credor_anterior}|"
        f"{debito_a_pagar_cofins}|0,00|0,00|{debito_a_pagar_cofins}|0,00|0,00|0,00|0,00|{debito_a_pagar_cofins}|"
    )
    contar_e_escrever(linha, arquivo)

def gerar_registro_m605(arquivo, dados_cnpj):
    if float(dados_cnpj['debito_a_pagar_cofins']) <= 0:
        return
    
    debito_a_pagar_cofins = formata_valor(dados_cnpj['debito_a_pagar_cofins'])
    contar_e_escrever(f'|M605|08|585601|{debito_a_pagar_cofins}|', arquivo)
    
def gerar_registro_m610(arquivo, dados_cnpj):
    contar_e_escrever(
        f"|M610|01|{formata_valor(dados_cnpj['valor_total_base_01'])}|{formata_valor(dados_cnpj['base_original_pis_cofins'])}|0,00|{formata_valor(dados_cnpj['credito_pis_cofins_icms_st'])}|"
        f"{formata_valor(dados_cnpj['base_pis_cofins_sem_icms_st'])}|7,6000|||{formata_valor(dados_cnpj['debito_cofins_do_mes'])}|0,00|0,00|0,00|0,00|"
        f"{formata_valor(dados_cnpj['debito_cofins_do_mes'])}|",
        arquivo
    )

def gerar_registro_m615(arquivo, dados_cnpj, cnpj, periodo):
    registro = (
        f"|M615|0|{formata_valor(dados_cnpj['credito_pis_cofins_icms_st'])}|42||Exclusão do valor do ICMS-ST destacado nas notas fiscais de entrada conforme Solução COSIT nº 100/2025.|{ultimo_dia_mes(periodo)}|2399|{cnpj}||"
    )
    
    contar_e_escrever(registro, arquivo)

def gerar_registro_m800(arquivo, dados_cnpj):
    base_04 = dados_cnpj['valor_total_base_04']
    base_05 = dados_cnpj['valor_total_base_05']
    base_06 = dados_cnpj['valor_total_base_06']
    base_07 = dados_cnpj['valor_total_base_07']
    base_08 = dados_cnpj['valor_total_base_08']
    base_09 = dados_cnpj['valor_total_base_09']

    # === 4) Escrita dos registros M400 ===
    if base_04 > 0:
        contar_e_escrever(
            f"|M800|04|{formata_valor(base_04)}|2398||", arquivo
        )
    
    if base_05 > 0:
        contar_e_escrever(
            f"|M800|05|{formata_valor(base_05)}|2398||", arquivo
        )
    
    if base_06 > 0:
        contar_e_escrever(
            f"|M800|06|{formata_valor(base_06)}|2398||", arquivo
        )
    
    if base_07 > 0:
        contar_e_escrever(
            f"|M800|07|{formata_valor(base_07)}|2398||", arquivo
        )
        
    if base_08 > 0:
        contar_e_escrever(
            f"|M800|08|{formata_valor(base_08)}|2398||", arquivo
        )
    
    if base_09 > 0:
        contar_e_escrever(
            f"|M800|09|{formata_valor(base_09)}|2398||", arquivo
        )

def gerar_registrom_810(arquivo, dados_cnpj):
    contar_e_escrever(f'|M810|102|{formata_valor(dados_cnpj["valor_total_base_06"])}|2399||', arquivo)

def gerar_arquivo_sped(dados):
    global contador_csts
    contador_csts = {}  # Inicializa o dicionário global
    
    os.makedirs('SPED CONTRIBUICOES MODIFICADO', exist_ok=True)
    
    for periodo, dados_periodo in sorted(dados.items()):

        contador_csts[periodo] = {}  # Inicializa o dicionário para o período
        dados_cnpj = dados_periodo
        print(dados_cnpj['emitente'])
        cnpj = dados_cnpj['emitente']['cnpj']
        contador_csts[periodo]= {}  # Inicializa o dicionário para o CNPJ
        
        nome_arquivo = f"SPED CONTRIBUICOES MODIFICADO/sped_retificador_{periodo}.txt"
        # data_inicial, data_final = obter_primeiro_e_ultimo_dia(periodo)
        emitente = dados_cnpj['emitente']
        razao_social_emitente = emitente['razao_social']
        # nome_fantasia_emitente = emitente['nome_fantasia']
        inscricao_estadual_emitente = emitente['inscricao_estadual']
        uf_emitente = emitente['UF']
        codigo_municipio_emitente = emitente['codigo_municipio']

        participantes = dados_cnpj['participantes']
        
        for nota in dados_cnpj['notas']:
            # notas.append(nota)
            natureza_operacao = nota['natureza_operação']
            if natureza_operacao not in naturezas:
                naturezas.append(natureza_operacao)

            informacao_complementar = nota['informacoes_complementares']
            if informacao_complementar not in informacoes_complementares:
                informacoes_complementares.append(informacao_complementar)
                
            for item in nota['itens']:
                
                if item['unidade'] not in dados_cnpj['unidades']:
                    dados_cnpj['unidades'].add(item['unidade'])
        
        notas = dados_cnpj['notas']
                    
        with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
            # Bloco 0
            gerar_registro_0000(periodo, razao_social_emitente, cnpj, inscricao_estadual_emitente, uf_emitente, codigo_municipio_emitente, arquivo)
            gerar_registro_0001(arquivo)
            gerar_registro_0100(arquivo)
            gerar_registro_0110(arquivo)
            gerar_registro_0111(arquivo, dados_cnpj)
            gerar_registro_0140(arquivo, razao_social_emitente, cnpj, uf_emitente, inscricao_estadual_emitente, codigo_municipio_emitente)
            mapa_codigos_participantes = gerar_registro_0150(participantes, arquivo)
            gerar_registro_0190(dados_cnpj['unidades'], arquivo)
            mapa_codigos_itens = gerar_registro_0200(dados_cnpj['itens'], arquivo)
            mapa_codigos_naturezas = gerar_registro_0400(naturezas, arquivo)
            # mapa_codigos_informacoes_complementares = gerar_registro_0450(informacoes_complementares, arquivo)
            gerar_registro_0500(arquivo)
            gerar_registro_0900(arquivo,dados_cnpj)
            contar_e_escrever(f'|0990|{contador_blocos['0'] + 1}|', arquivo)
            ''
            gerar_bloco_a(arquivo)
            
            gerar_bloco_c(arquivo, cnpj)
            gerar_registro_c100(notas, mapa_codigos_participantes, arquivo, periodo, cnpj, mapa_codigos_itens, mapa_codigos_naturezas)
            contar_e_escrever(f'|C990|{contador_blocos['C'] + 1}|', arquivo)
            
            gerar_registro_d001(arquivo)
            gerar_registro_d010(arquivo, dados_cnpj, cnpj)
            gerar_registro_d100(arquivo, dados_cnpj, mapa_codigos_participantes)
            contar_e_escrever(f'|D990|{contador_blocos['D'] + 1}|', arquivo)
            
            gerar_registro_f001(arquivo)
            # gerar_registro_f010(arquivo, cnpj)
            # gerar_registro_f100(arquivo)
            contar_e_escrever(f'|F990|{contador_blocos['F'] + 1}|', arquivo)
            
            gerar_registro_i001(arquivo)
            contar_e_escrever(f'|I990|{contador_blocos['I'] + 1}|', arquivo)
            
            gerar_registro_m001(arquivo)
            
            gerar_registro_m100(arquivo, dados_cnpj)
            
            gerar_registro_m200(arquivo, dados_cnpj)
            gerar_registro_m205(arquivo, dados_cnpj)
            gerar_registro_m210(arquivo, dados_cnpj)
            gerar_registro_m215(arquivo, dados_cnpj, cnpj, periodo)
            
            gerar_registro_m400(arquivo, dados_cnpj)
            gerar_registro_m410(arquivo, dados_cnpj)
            
            gerar_registro_m500(arquivo, dados_cnpj)
            
            gerar_registro_m600(arquivo, dados_cnpj)
            gerar_registro_m605(arquivo, dados_cnpj)
            gerar_registro_m610(arquivo, dados_cnpj)
            gerar_registro_m615(arquivo, dados_cnpj, cnpj, periodo)
            
            gerar_registro_m800(arquivo, dados_cnpj)
            gerar_registrom_810(arquivo, dados_cnpj)
            
            contar_e_escrever(f'|M990|{contador_blocos['M'] + 1}|', arquivo)
                            
            contar_e_escrever('|P001|1|', arquivo)
            contar_e_escrever('|P990|2|', arquivo)
            
            saldo_credor_anterior = float(dados_cnpj.get('saldo_credor_anterior_pis', 0) or 0.0)

            if saldo_credor_anterior <= 0:
                contar_e_escrever('|1001|1|', arquivo)
                contar_e_escrever('|1990|2|', arquivo)
            else : 
                contar_e_escrever('|1001|0|', arquivo)
                gerar_registro_1100(arquivo, dados_cnpj, periodo)
                gerar_registro_1500(arquivo, dados_cnpj, periodo)
                contar_e_escrever('|1990|4|', arquivo)

            gerar_bloco_9(arquivo)
            
            
        print(f"Arquivo SPED Retificador gerado com sucesso: {nome_arquivo}")



