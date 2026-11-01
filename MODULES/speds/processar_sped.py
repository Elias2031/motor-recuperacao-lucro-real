from MODULES.config_ambiente import CONSUMIDOR_PADRAO_CPF
from pathlib import Path
import re
from MODULES.utilitarios import _periodo_arquivo
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

global saldo_credor
saldo_credor = 0 

def _to_dec(x):
    """Converte valores SPED em Decimal, tolerando milhar, vírgula, espaços, etc."""
    if x is None:
        return Decimal('0')
    if isinstance(x, Decimal):
        return x
    if isinstance(x, (int, float)):
        return Decimal(str(x))

    s = str(x).strip()
    if not s:
        return Decimal('0')

    # trata sinal em parênteses: (123,45) -> -123,45
    neg = False
    if s.startswith('(') and s.endswith(')'):
        neg = True
        s = s[1:-1].strip()

    # remove espaços e NBSP
    s = s.replace('\xa0', '').replace(' ', '')

    # remove separadores de milhar (.)
    s = s.replace('.', '')

    # vírgula decimal -> ponto
    s = s.replace(',', '.')

    # mantém apenas dígitos, ponto e sinal
    s2 = ''.join(ch for ch in s if ch.isdigit() or ch in '.-')
    if s2.count('.') > 1:
        # se sobrar mais de um '.', junta tudo e deixa apenas o último como decimal
        parts = s2.split('.')
        s2 = ''.join(parts[:-1]) + '.' + parts[-1]

    try:
        val = Decimal(s2 or '0')
    except InvalidOperation:
        val = Decimal('0')

    return -val if neg else val

def split_sped(linha: str):
    # '|E110|...|\n' -> ['E110', '...', ...]
    p = linha.rstrip('\n').split('|')
    if p and p[0] == '':
        p = p[1:]
    if p and p[-1] == '':
        p = p[:-1]
    return p

def join_sped(campos: list[str]) -> str:
    return '|' + '|'.join(campos) + '|\n'

def formatar_valor_sped(valor, casas=2) -> str:
    """
    Formata um número para o padrão SPED:
    - vírgula como separador decimal
    - sem separador de milhar
    - arredondamento HALF_UP (financeiro)
    - tolera str com '.' ou ',' e None

    Ex.: 1858.4799999993 -> '1858,48'
    """
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return f"0,{('0'*casas) if casas > 0 else ''}" if casas else "0"

    # Converte string com vírgula para ponto; remove milhar se vier como string
    if isinstance(valor, str):
        bruto = valor.strip().replace('.', '').replace(',', '.')
    else:
        bruto = str(valor)

    try:
        d = Decimal(bruto)
    except InvalidOperation:
        # fallback seguro
        return f"0,{('0'*casas) if casas > 0 else ''}" if casas else "0"

    # Arredondamento financeiro
    quant = Decimal(10) ** (-casas)
    d = d.quantize(quant, rounding=ROUND_HALF_UP)

    # Evita '-0,00'
    if d == Decimal('-0'):
        d = Decimal('0')

    s = f"{d:.{casas}f}" if casas > 0 else f"{d:.0f}"
    return s.replace('.', ',')

def alterar_sped(arquivo_sped, itens_bloco_e, qtd_itens_errados, itens_bloco_0200, unidades_unicas, dados_empresa):
    removeu_e116 = False
    contador_0221_adicionado = 0
    """
    Altera um arquivo SPED aplicando:
      - Injeção de unidades (|0190|) que não existirem no arquivo.
      - Deduplicação e inserção de itens do bloco |0200|.
      - Ajustes nos registros de controle |9900|, |9990|, |9999| conforme linhas inseridas.
      - Atualizações em registros do bloco E (|E110|, |E111|, |E116|) conforme 'dados_empresa'.
      - Injeção de participante padrão no |0150|.
      - Limitação do tamanho de descrições em |0450| e |0460| (máx. 200 chars).
    """

    # -------------------------------------------------------------
    # 1) Ler o arquivo original e coletar COD_ITEM e UNID já existentes
    # -------------------------------------------------------------
    cod_itens_existentes = set()         # COD_ITEM já declarados em |0200|
    unidades_0190_existentes = set()     # Unidades já declaradas em |0190|

    with open(arquivo_sped, 'r', encoding='utf-8', errors='ignore') as arq_inicial:
        for linha_lida in arq_inicial:
            # Coleta unidades do registro 0190
            if linha_lida.startswith('|0190|'):
                partes_0190 = linha_lida.strip().split('|')
                if len(partes_0190) > 2 and partes_0190[2]:
                    unidades_0190_existentes.add(partes_0190[2])

            # Coleta COD_ITEM do registro 0200
            if linha_lida.startswith('|0200|'):
                partes_0200 = linha_lida.strip().split('|')
                if len(partes_0200) > 2 and partes_0200[2]:
                    cod_itens_existentes.add(partes_0200[2])

    # Unidades novas = as recebidas que ainda não existem no arquivo
    unidades_novas = sorted(u for u in unidades_unicas if u and u not in unidades_0190_existentes)
    tem_0190_no_arquivo = bool(unidades_0190_existentes)

    # -------------------------------------------------------------
    # 2) Filtrar/normalizar os |0200| de entrada, deduplicando por COD_ITEM
    # -------------------------------------------------------------
    # Mantém a primeira ocorrência de cada COD_ITEM que não exista no arquivo
    novos_por_cod = {}  # COD_ITEM -> linha completa original
    for item in itens_bloco_0200:
        if not item:
            continue
        linha_item_0200 = item.strip()
        if not linha_item_0200.startswith('|0200|'):
            continue

        partes = linha_item_0200.split('|')
        if len(partes) <= 2 or not partes[2]:
            # ignora linhas malformadas
            continue

        cod_item = partes[2]
        # Só entra se não existir no arquivo e ainda não tiver sido adicionado
        if cod_item not in cod_itens_existentes and cod_item not in novos_por_cod:
            novos_por_cod[cod_item] = linha_item_0200

    # -------------------------------------------------------------
    # 3) Ordenar por COD_ITEM (determinístico) e calcular quantidade
    # -------------------------------------------------------------
    itens_bloco_0200 = [novos_por_cod[c] for c in sorted(novos_por_cod)]
    qtd_itens_0200 = len(itens_bloco_0200)

    # -------------------------------------------------------------
    # 4) Preparar diretório/arquivo de saída
    # -------------------------------------------------------------
    pasta_saida = Path('SPEDS_MODIFICADOS')
    pasta_saida.mkdir(parents=True, exist_ok=True)
    nome_sped_modificado = f"MODIFICADO_{Path(arquivo_sped).name}"
    caminho_saida = pasta_saida / nome_sped_modificado

    # Flags de injeção controlada (mantidas da lógica original)
    injetou_apos_primeiro_0190 = False
    injetou_consumidor_padrao = False

    # -------------------------------------------------------------
    # 5) Abrir arquivos e processar linha a linha
    # -------------------------------------------------------------
    with open(arquivo_sped, 'r', encoding='utf-8', errors='ignore') as arq_entrada:
        linhas = arq_entrada.readlines()

    with open(f'{caminho_saida}', 'w', encoding='utf-8', errors='ignore') as arq_saida:

        # Variáveis de controle de escrita (respeitando fluxo original)
        escreve = True
        escreve_0200 = True

        i = 0
        while i < len(linhas):
            linha = linhas[i]
            proxima = linhas[i+1] if i + 1 < len(linhas) else None
            escreve = True  # reset por iteração

            # Força o campo [3] do |0000| para '1'
            if linha.startswith('|0000|'):
                campos_0000 = linha.strip().split('|')
                campos_0000[3] = '1'
                arq_saida.write('|'.join(campos_0000) + '\n')
                escreve = False
                i += 1
                continue

            # Injeta participante padrão logo após o primeiro |0150|
            if not injetou_consumidor_padrao and linha.startswith('|0150|'):
                arq_saida.write(linha)  # mantém a linha original
                arq_saida.write(f'|0150|MPH007|CONSUMIDOR FINAL PADRAO|1058||{CONSUMIDOR_PADRAO_CPF}||5300108||ENDERECO|S/N|||\n')
                injetou_consumidor_padrao = True
                i += 1
                continue  # evita reescrita dessa linha

            # Injeções de |0190|
            if linha.startswith('|0190|'):
                if not injetou_apos_primeiro_0190 and unidades_novas:
                    # Mantém o primeiro 0190 original e injeta os novos em seguida
                    arq_saida.write(linha)
                    for unid in unidades_novas:
                        arq_saida.write(f'|0190|{unid}|Unidade Importada Nfe|\n')
                    injetou_apos_primeiro_0190 = True
                    i += 1
                    continue  # já foi escrita
                else:
                    # Demais |0190| originais são mantidos
                    arq_saida.write(linha)
                    i += 1
                    continue

            # Se o arquivo não tinha nenhum |0190|, injeta todos ANTES do |0990|
            if linha.startswith('|0990|') and (not tem_0190_no_arquivo) and unidades_novas:
                for unid in unidades_novas:
                    arq_saida.write(f'|0190|{unid}|Unidade Importada Nfe|\n')
                # não dá continue aqui; deixa cair para a lógica do |0990| abaixo
                # para ajustar contagem, etc.

            # Ajuste do contador em |9900|0150|
            if linha.startswith('|9900|0150|'):
                o9900_0150 = [linha.strip().split('|')]
                o9900_0150[0][3] = str(int(o9900_0150[0][3]) + 1)
                arq_saida.write('|'.join(o9900_0150[0]) + '\n')
                escreve = False
                i += 1
                continue

            # Ajuste do contador em |9900|0190|
            if linha.startswith('|9900|0190|'):
                o9900_0190 = [linha.strip().split('|')]
                o9900_0190[0][3] = str(int(o9900_0190[0][3]) + len(unidades_novas))
                arq_saida.write('|'.join(o9900_0190[0]) + '\n')
                escreve = False
                i += 1
                continue

            # ===========================
            # INSERÇÃO DOS NOVOS |0200|
            # ===========================
            
            if linha.startswith('|0200|'):
                # 0) Parse do COD_ITEM do 0200 original
                campos_0200 = linha.strip().split('|')
                codigo_item_original = campos_0200[2] if len(campos_0200) > 2 else ''
                codigo_tipo_item = campos_0200[7] if len(campos_0200) > 7 else ''
                
                # 1) Escreve o |0200| original
                arq_saida.write(linha)

                # 2) Escreve todos os |0220| contíguos
                j = i + 1
                while j < len(linhas) and linhas[j].startswith('|0220|'):
                    arq_saida.write(linhas[j])
                    j += 1

                # 3) Copia |0221| contíguos e checa se algum corresponde ao COD_ITEM do 0200
                tem_0221_do_mesmo_item = False
                k = j
                while k < len(linhas) and linhas[k].startswith('|0221|'):
                    campos_221 = linhas[k].strip().split('|')
                    # |0221|COD_ITEM_ATOMICO|QTD_CONV|
                    if len(campos_221) > 2 and campos_221[2] == codigo_item_original:
                        tem_0221_do_mesmo_item = True
                    arq_saida.write(linhas[k])
                    k += 1

                if not tem_0221_do_mesmo_item and codigo_tipo_item == '00':
                    # Injeta um 0221 mínimo; ajuste a QTD_CONV se necessário
                    arq_saida.write(f'|0221|{codigo_item_original}|1|\n')
                    contador_0221_adicionado += 1

                # 4) Injeta seus novos 0200 + 0221 apenas uma vez (ponto de injeção)
                if escreve_0200:
                    for linha_item in itens_bloco_0200:
                        codigo_item = (linha_item.strip().split('|')[2]
                                    if '|' in linha_item else '')
                        arq_saida.write(linha_item.rstrip('\n') + '\n')  # |0200| novo
                        arq_saida.write(f'|0221|{codigo_item}|1|\n')     # |0221| filho
                    escreve_0200 = False

                # 5) Avança o índice para depois do bloco (0200 + 0220/0221 contíguos)
                i = k
                continue

            # Trunca descrição de |0450| para 200 chars (se necessário)
            if linha.startswith('|0450|'):
                campos_0450 = linha.strip().split('|')
                if len(campos_0450[3]) > 200:
                    campos_0450[3] = campos_0450[3][:200].strip()
                    arq_saida.write('|'.join(campos_0450) + '\n')
                    escreve = False
                    i += 1
                    continue

            # Trunca descrição de |0460| para 200 chars (se necessário)
            if linha.startswith('|0460|'):
                campos_0460 = linha.strip().split('|')
                if len(campos_0460[3]) > 200:
                    campos_0460[3] = campos_0460[3][:200].strip()
                    arq_saida.write('|'.join(campos_0460) + '\n')
                    escreve = False
                    i += 1
                    continue

            # Ajusta totalizador |0990| somando linhas adicionadas (0200 + 0190 + 1)
            if linha.startswith('|0990|'):
                o0990 = [linha.strip().split('|')]
                o0990[0][2] = str(int(o0990[0][2]) + (qtd_itens_0200 * 2) + len(unidades_novas) + 1 + contador_0221_adicionado)
                arq_saida.write('|'.join(o0990[0]) + '\n')
                escreve = False
                i += 1
                continue

            # ------------------------------------------------------------------
            # Bloco E: atualizações de |E110| (mantido como no código original)
            # ------------------------------------------------------------------
            if linha.startswith('|E110|'):
                global saldo_credor

                campos = split_sped(linha)
                dados_empresa['saldo_credor_anterior'] = saldo_credor
                
                # Índices do E110
                IND_REGISTRO = 0
                IND_VALOR_TOTAL_DEBITOS = 1
                IND_VALOR_AJUSTES_DEBITOS_POR_DOCUMENTO = 2
                IND_VALOR_AJUSTES_DEBITOS_POR_APURACAO = 3
                IND_VALOR_ESTORNOS_DE_CREDITOS = 4

                IND_VALOR_TOTAL_CREDITOS = 5
                IND_VALOR_AJUSTES_CREDITOS_POR_DOCUMENTO = 6
                IND_VALOR_AJUSTES_CREDITOS_POR_APURACAO = 7
                IND_VALOR_ESTORNOS_DE_DEBITOS = 8

                IND_VALOR_SALDO_CREDOR_PERIODO_ANTERIOR = 9
                IND_VALOR_SALDO_DEVEDOR_APURADO = 10
                IND_VALOR_TOTAL_DEDUCOES = 11
                IND_VALOR_ICMS_A_RECOLHER = 12
                IND_VALOR_SALDO_CREDOR_A_TRANSPORTAR = 13
                IND_VALOR_RECOLHIMENTO_EXTRAORDINARIO = 14
                
                dados_empresa['debito_original_icms'] = float(campos[IND_VALOR_ICMS_A_RECOLHER].replace(',','.'))

                # 1) saldo credor anterior
                campos[IND_VALOR_SALDO_CREDOR_PERIODO_ANTERIOR] = formatar_valor_sped(saldo_credor)

                # 2) Crédito a recuperar → soma em estornos de débitos
                valor_estornos_de_debitos_atualizado = (
                    _to_dec(campos[IND_VALOR_ESTORNOS_DE_DEBITOS]) +
                    _to_dec(dados_empresa.get('soma_valores_a_recuperar_icms', 0))
                )
                campos[IND_VALOR_ESTORNOS_DE_DEBITOS] = formatar_valor_sped(valor_estornos_de_debitos_atualizado)

                # 3) Totais
                total_debitos = (
                    _to_dec(campos[IND_VALOR_TOTAL_DEBITOS]) +
                    _to_dec(campos[IND_VALOR_AJUSTES_DEBITOS_POR_DOCUMENTO]) +
                    _to_dec(campos[IND_VALOR_AJUSTES_DEBITOS_POR_APURACAO]) +
                    _to_dec(campos[IND_VALOR_ESTORNOS_DE_CREDITOS])
                )
                total_creditos = (
                    _to_dec(campos[IND_VALOR_TOTAL_CREDITOS]) +
                    _to_dec(campos[IND_VALOR_AJUSTES_CREDITOS_POR_DOCUMENTO]) +
                    _to_dec(campos[IND_VALOR_AJUSTES_CREDITOS_POR_APURACAO]) +
                    _to_dec(campos[IND_VALOR_ESTORNOS_DE_DEBITOS]) +
                    _to_dec(campos[IND_VALOR_SALDO_CREDOR_PERIODO_ANTERIOR])
                )

                saldo_apurado = total_debitos - total_creditos

                if saldo_apurado > 0:
                    campos[IND_VALOR_SALDO_DEVEDOR_APURADO] = formatar_valor_sped(saldo_apurado)
                    icms_a_recolher = saldo_apurado - _to_dec(campos[IND_VALOR_TOTAL_DEDUCOES])
                    campos[IND_VALOR_ICMS_A_RECOLHER] = formatar_valor_sped(icms_a_recolher if icms_a_recolher > 0 else 0)
                    campos[IND_VALOR_SALDO_CREDOR_A_TRANSPORTAR] = '0,00'
                    saldo_credor = 0
                else:
                    campos[IND_VALOR_SALDO_DEVEDOR_APURADO] = '0,00'
                    campos[IND_VALOR_ICMS_A_RECOLHER] = '0,00'
                    campos[IND_VALOR_SALDO_CREDOR_A_TRANSPORTAR] = formatar_valor_sped(-saldo_apurado)
                    saldo_credor = _to_dec(campos[IND_VALOR_SALDO_CREDOR_A_TRANSPORTAR])

                if len(campos) <= IND_VALOR_RECOLHIMENTO_EXTRAORDINARIO:
                    campos += [''] * (IND_VALOR_RECOLHIMENTO_EXTRAORDINARIO - len(campos) + 1)
                if not campos[IND_VALOR_RECOLHIMENTO_EXTRAORDINARIO].strip():
                    campos[IND_VALOR_RECOLHIMENTO_EXTRAORDINARIO] = '0,00'

                linha_atualizada = join_sped(campos)
                arq_saida.write(linha_atualizada)

                # Injeta |E111| e depois as linhas do bloco E fornecidas
                arq_saida.write(
                    f"|E111|DF030599|Vendas de itens com redução da base, destacado erroneamente o valor da aliquota integral|{formatar_valor_sped(dados_empresa['soma_valores_a_recuperar_icms'])}|\n"
                )
                for linha_item_E in itens_bloco_e:
                    arq_saida.write(linha_item_E + '\n')
                escreve = False

                dados_empresa['debito_icms'] = float(campos[IND_VALOR_TOTAL_DEBITOS].replace(',','.'))
                dados_empresa['debito_a_pagar_icms'] = float(campos[IND_VALOR_ICMS_A_RECOLHER].replace(',','.'))
                dados_empresa['saldo_credor_a_transportar'] = saldo_credor

                i += 1
                continue

            # Ajusta |9900|E111| inserindo o contador de |E113|
            if linha.startswith('|9900|E111|'):
                arq_saida.write(f'|9900|E113|{qtd_itens_errados}|\n')
                i += 1
                continue

            # Atualiza |E116|
            if linha.startswith('|E116|') and saldo_credor <= 0:
                e116 = [linha.strip().split('|')]
                valor_obrigacao_a_recolher = e116[0][3]
                valor_obrigacao_a_recolher_atualizado = float(valor_obrigacao_a_recolher.replace(',', '.')) - dados_empresa['soma_valores_a_recuperar_icms']
                e116[0][3] = formatar_valor_sped(valor_obrigacao_a_recolher_atualizado)
                arq_saida.write('|'.join(e116[0]) + '\n')
                escreve = False
                i += 1
                continue
            if linha.startswith('|E116|') and saldo_credor > 0:
                removeu_e116 = True
                escreve = False
                i += 1
                continue

            # Ajusta |9900|0200|
            if linha.startswith('|9900|0200|'):
                o9900_0200 = [linha.strip().split('|')]
                o9900_0200[0][3] = str(int(o9900_0200[0][3]) + qtd_itens_0200)
                arq_saida.write('|'.join(o9900_0200[0]) + '\n')
                escreve = False
                i += 1
                continue

            # Ajusta |9900|0221|
            if linha.startswith('|9900|0221|'):
                o9900_0221 = [linha.strip().split('|')]
                o9900_0221[0][3] = str(int(o9900_0221[0][3]) + qtd_itens_0200)
                arq_saida.write('|'.join(o9900_0221[0]) + '\n')
                escreve = False
                i += 1
                continue

            # Ajusta |E990|
            if linha.startswith('|E990|'):
                e990 = [linha.strip().split('|')]
                if removeu_e116:
                    e990[0][2] = str(int(e990[0][2]) + qtd_itens_errados)
                else:
                    e990[0][2] = str(int(e990[0][2]) + qtd_itens_errados + 1)
                arq_saida.write('|'.join(e990[0]) + '\n')
                escreve = False
                i += 1
                continue

            # Injeta contadores após |9900|E110|
            if linha.startswith('|9900|E110|'):
                arq_saida.write(linha)
                arq_saida.write('|9900|E111|1|\n')
                arq_saida.write(f'|9900|E113|{qtd_itens_errados}|\n')
                escreve = False
                i += 1
                continue

            if linha.startswith('|9900|E116|') and removeu_e116:
                campos = [linha.strip().split('|')]
                campos[0][3] = '0'
                arq_saida.write('|'.join(campos[0]) + '\n')
                escreve = False
                i += 1
                continue

            # Ajusta |9900|9900|
            if linha.startswith('|9900|9900|'):
                o9900_9900 = [linha.strip().split('|')]
                o9900_9900[0][3] = str(int(o9900_9900[0][3]) + 2)
                arq_saida.write('|'.join(o9900_9900[0]) + '\n')
                escreve = False
                i += 1
                continue

            # Ajusta |9990|
            if linha.startswith('|9990|'):
                a9990 = [linha.strip().split('|')]
                a9990[0][2] = str(int(a9990[0][2]) + 2)
                arq_saida.write('|'.join(a9990[0]) + '\n')
                escreve = False
                i += 1
                continue

            # Ajusta |9999| e finaliza'
            if linha.startswith('|9999|'):
                c9999 = [linha.strip().split('|')]
                if removeu_e116:
                    c9999[0][2] = str(int(c9999[0][2]) + qtd_itens_errados + (qtd_itens_0200 * 2) + len(unidades_novas) + 3 + contador_0221_adicionado)
                else:
                    c9999[0][2] = str(int(c9999[0][2]) + qtd_itens_errados + (qtd_itens_0200 * 2) + len(unidades_novas) + 3 + 1 + contador_0221_adicionado)

                arq_saida.write('|'.join(c9999[0]) + '\n')
                # encerra conforme o fluxo original
                return

            # ---------------------------------------------------------
            # Escrita padrão da linha original (se não foi interceptada)
            # ---------------------------------------------------------
            if escreve:
                arq_saida.write(linha)

            i += 1

def processar_speds(dados_por_periodo_e_cnpj):
    for periodo in sorted(dados_por_periodo_e_cnpj.keys()):            
            dados_empresa = dados_por_periodo_e_cnpj[periodo]
            
            # if dados_empresa['soma_valores_a_recuperar_icms'] > 0:                 
            base = Path('SPED')

            candidatos = [p for p in base.iterdir() if p.is_file() and _periodo_arquivo(p.name) == periodo ]

            if not candidatos:
                print(f"Nenhum arquivo SPED encontrado para o período {periodo} - retificando SPED")
            else:
                # Dá prioridade para entrega '0' (original)
                candidatos.sort(key=lambda p: int(re.search(r'-(\d)-', p.name).group(1)) if re.search(r'-(\d)-', p.name) else 9)
                
                for candidato in candidatos :
                    alterar_sped(candidato, dados_empresa['itens_bloco_e'], dados_empresa['qtd_itens_errados'], dados_empresa['itens_bloco_0200'], dados_empresa['unidades'], dados_empresa)