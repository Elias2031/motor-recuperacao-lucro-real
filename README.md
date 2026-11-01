# Motor de Recuperação Tributária: Lucro Real

> Este sistema está sendo substituído por agentes de IA; o código foi aberto como portfólio e referência.

Motor em Python que reprocessa os XMLs fiscais de uma empresa do **Lucro Real** para encontrar tributo pago a maior: **créditos de PIS/COFINS** não aproveitados nas entradas e **ICMS destacado a maior** nas saídas. Ao final ele gera os arquivos **SPED retificadores** e as planilhas de apoio.

Repositório irmão: [MOTOR_RECUPERACAO_SN](https://github.com/Elias2031/MOTOR_RECUPERACAO_SN), a mesma ideia aplicada a empresas do **Simples Nacional** (segregação de receitas monofásicas/ST e reapuração do PGDAS-D).

---

## O problema de negócio

Na recuperação tributária, o escritório revisa os últimos 5 anos da empresa atrás de valores pagos indevidamente. No Lucro Real (regime não cumulativo de PIS/COFINS) as fontes mais comuns são:

- **Créditos de PIS/COFINS não tomados** nas compras para revenda, nos insumos e nos fretes (CT-e) quando a empresa é tomadora.
- **Classificação errada de CST PIS/COFINS nas vendas**: produto monofásico, de alíquota zero ou com ST tributado como alíquota básica.
- **ICMS destacado com a alíquota cheia** em item que tem redução de base de cálculo, ou ICMS próprio destacado em item sujeito a ST.

Fazer isso à mão, nota a nota e mês a mês, é inviável. O motor automatiza a leitura dos XMLs, a comparação com a análise tributária por NCM e a montagem das escriturações retificadoras.

## Como o motor funciona

### Entradas (pastas no diretório de execução)

| Pasta | Conteúdo |
|---|---|
| `notas_fiscais/` | ZIPs com os XMLs. O nome do ZIP define o tipo: contém `cte` → CT-e de entrada; contém `dest`/`destinatário` → NF-e de entrada; qualquer outro → NF-e de saída. XMLs começando com `CANCELADO` são ignorados. |
| `ANALISE/` | Planilha `.xlsx` de análise tributária por NCM (o primeiro arquivo da pasta é usado). Colunas usadas: `NCM`, `NOME ITEM NOTA`, `CST ICMS`, `CST PIS COFINS`, `CEST`, `ALIQUOTA ICMS RETORNADO`, `ALIQUOTA REDUCAO INTERNA`, `ALIQUOTA REDUCAO EXTERNA`. |
| `SPED/` | EFD ICMS/IPI (SPED Fiscal) originais da empresa. O período é lido do nome do arquivo (`...-AAAAMMDD-AAAAMMDD-...`); a entrega original (`-0-`) tem prioridade. |
| `_RECURSOS_/` | Tabelas públicas versionadas: `tipi.xlsx` (TIPI) e `cfop_creditos_pis_cofins_nat_operacao.txt` (CFOP → natureza da base de crédito, tabela 4.3.7 da EFD-Contribuições). |

### Regras aplicadas

1. **Leitura dos XMLs** (`MODULES/processar_xml/`): NF-e de saída, NF-e de entrada (incluindo devoluções) e CT-e, agrupados por período (`AAAA-MM`). Notas repetidas são descartadas pela chave.
2. **Correspondência por NCM** (`MODULES/utilitarios.py`): cada item é casado com a linha da planilha de análise de mesmo NCM e descrição mais parecida (similaridade de texto). Itens sem correspondência vão para `Itens sem correspondência.xlsx`.
3. **ICMS a recuperar nas saídas** (`processar_notas_saidas.py`): recalcula o ICMS com a alíquota interna e a redução de base da análise (alíquota interestadual de 12% fora do DF e tratamento à parte, a partir de 2025, dos itens de alíquota interna de 18%). Em item com ST o ICMS próprio destacado é todo recuperável. A diferença vira registro `E113`.
4. **Reclassificação de CST PIS/COFINS** das saídas (01, 04, 05, 06...) e acumulação da receita por CST.
5. **Créditos de PIS/COFINS nas entradas** (`MODULES/apuracoes/apurar_pis_cofins.py`): por CST e alíquota, com o código de crédito da tabela 4.3.6 (grupos 100/200/300) e a natureza da base pelo CFOP. Os CT-e em que a empresa é tomadora também geram crédito.

### Saídas

| Saída | Origem |
|---|---|
| `SPEDS_MODIFICADOS/MODIFICADO_<arquivo>` | SPED Fiscal retificado: injeta `0190`/`0200` faltantes, participante padrão no `0150`, ajuste `E111` + `E113` por item, recalcula `E110`/`E116` e os totalizadores do bloco 9. |
| `SPED CONTRIBUICOES MODIFICADO/` | EFD-Contribuições gerada do zero por período: blocos 0, A, C (`C100/C170/C175/C190`), D (`D100/D101/D105`), F, M (`M100/M105/M200/M210/M500/M505/M600/M610/M800`...), 1 (`1100/1500`) e 9. |
| `relatorios_apuracao/<periodo>.txt` | Memória de cálculo do crédito de PIS/COFINS. |
| `RELATORIOS/`, `RELATORIOS_1/` | Relatórios mensais em texto. |
| `apuracao_por_periodo.xlsx` | Apuração consolidada de todos os períodos. |
| `PLANILHAS DE ITENS A RECUPERAR ICMS/`, `PLANILHAS DE CREDITO PIS COFINS/` | Planilhas item a item para conferência e para o dossiê do cliente. |

## Stack

- Python 3.12+ (o código usa f-strings com aspas aninhadas, PEP 701)
- `pandas` e `openpyxl` (planilhas), `xml.etree` e `zipfile` (XMLs), `PyPDF2`, `pyautogui` (alerta final)
- Sem banco de dados: o estado fica em memória num dicionário por período/CNPJ (`MODULES/public.py`)

## Como executar

```bash
python -m venv venv
venv\Scripts\activate            # Windows
pip install -r requirements.txt

copy .env.example .env           # preencha os dados do contabilista (registro 0100)

# monte as pastas de entrada: notas_fiscais/, ANALISE/, SPED/
python teste.py
```

O ponto de entrada é `teste.py` (`comecar_apurar()`), que roda o fluxo inteiro: XMLs → NCMs não encontrados → SPED Fiscal → PIS/COFINS → EFD-Contribuições → relatórios → planilhas.

### Variáveis de ambiente

Veja `.env.example`. Nenhuma é obrigatória para o código rodar, mas sem elas o SPED sai com placeholders e não passa no PVA.

- `CONTABILISTA_*`: dados do registro 0100 (nome, CPF, CRC, CNPJ do escritório, endereço, telefone, e-mail, município).
- `EMITENTE_*`: emitente padrão, usado só quando o período não tem nota de saída (com notas de saída os dados vêm do XML).
- `CONSUMIDOR_PADRAO_CPF`: documento do participante "CONSUMIDOR FINAL PADRAO" injetado no SPED Fiscal.

## Observações

- Algumas regras são específicas do **Distrito Federal** (código de ajuste `DF030599`, município padrão 5300108, alíquota interna). Para outra UF elas precisam ser revistas.
- Os documentos fiscais dos clientes não fazem parte do repositório; o `.gitignore` bloqueia XML, ZIP, PDF, planilhas e as pastas de entrada/saída.
- O resultado é material de apoio: a retificação e o pedido de restituição/compensação continuam sob responsabilidade do contador.

## Licença

MIT. Veja [LICENSE](LICENSE).

Autor: Elias Silva ([@Elias2031](https://github.com/Elias2031)), Morpho Automações.
