"""
Configuração lida de variáveis de ambiente (ou de um arquivo .env, se o
pacote python-dotenv estiver instalado). Veja .env.example.

Nenhum dado real de contador, escritório ou cliente fica no código.
"""
import os

try:
    from dotenv import load_dotenv  # opcional
    load_dotenv()
except ImportError:
    pass


def _env(nome, padrao=''):
    return os.getenv(nome, padrao).strip()


# Registro 0100 (dados do contabilista) do SPED gerado
CONTABILISTA = {
    'nome': _env('CONTABILISTA_NOME', 'NOME DO CONTABILISTA'),
    'cpf': _env('CONTABILISTA_CPF', '00000000000'),
    'crc': _env('CONTABILISTA_CRC', '000000O'),
    'cnpj_escritorio': _env('CONTABILISTA_CNPJ', ''),
    'cep': _env('CONTABILISTA_CEP', '00000000'),
    'endereco': _env('CONTABILISTA_ENDERECO', 'ENDERECO DO CONTABILISTA'),
    'numero': _env('CONTABILISTA_NUMERO', ''),
    'complemento': _env('CONTABILISTA_COMPLEMENTO', ''),
    'bairro': _env('CONTABILISTA_BAIRRO', 'BAIRRO'),
    'telefone': _env('CONTABILISTA_TELEFONE', ''),
    'fax': _env('CONTABILISTA_FAX', ''),
    'email': _env('CONTABILISTA_EMAIL', 'contato@exemplo.com.br'),
    'cod_municipio': _env('CONTABILISTA_COD_MUNICIPIO', '5300108'),
}


def registro_0100():
    c = CONTABILISTA
    return (
        f"|0100|{c['nome']}|{c['cpf']}|{c['crc']}|{c['cnpj_escritorio']}|{c['cep']}|"
        f"{c['endereco']}|{c['numero']}|{c['complemento']}|{c['bairro']}|{c['telefone']}|"
        f"{c['fax']}|{c['email']}|{c['cod_municipio']}|"
    )


# Emitente padrão usado quando o período só tem notas de entrada
# (é sobrescrito pelos dados do XML assim que uma nota de saída é lida)
EMITENTE_PADRAO = {
    "razao_social": _env('EMITENTE_RAZAO_SOCIAL', 'EMPRESA EXEMPLO LTDA'),
    "nome_fantasia": _env('EMITENTE_NOME_FANTASIA', 'EMPRESA EXEMPLO'),
    "inscricao_estadual": _env('EMITENTE_IE', ''),
    "UF": _env('EMITENTE_UF', 'DF'),
    "codigo_municipio": _env('EMITENTE_COD_MUNICIPIO', '5300108'),
    "cnpj": _env('EMITENTE_CNPJ', '00000000000000'),
    "cep": _env('EMITENTE_CEP', '00000000'),
    "logradouro": _env('EMITENTE_LOGRADOURO', 'ENDERECO'),
    "numero_logradouro": _env('EMITENTE_NUMERO', 'S/N'),
    "bairro": _env('EMITENTE_BAIRRO', 'BAIRRO'),
    "telefone": _env('EMITENTE_TELEFONE', ''),
    "codigo_pais": "1058",
}

# Documento (CPF) do participante "CONSUMIDOR FINAL PADRAO" injetado no SPED Fiscal
CONSUMIDOR_PADRAO_CPF = _env('CONSUMIDOR_PADRAO_CPF', '00000000000')
