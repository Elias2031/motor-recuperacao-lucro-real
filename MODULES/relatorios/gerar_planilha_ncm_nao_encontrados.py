from pyautogui import alert # type: ignore
from MODULES.processar_xml.processar_notas_saidas import ncm_nao_encontrados
import pandas as pd # type: ignore

def gerar_planilha_ncm_nao_encontrados():
    if len(ncm_nao_encontrados) > 1:
        df = pd.DataFrame(ncm_nao_encontrados[1:], columns=ncm_nao_encontrados[0])
        df.to_excel('Itens sem correspondência.xlsx', index=False)
        alert(text=f'{len(ncm_nao_encontrados) - 1} Itens não foram analisados corretamente. Por favor, verifique a tabela de NCMs sem correspondência.', title='Segregador Simples Nacional', button='OK')
    else:
        alert(text=f'Segregação finalizada com SUCESSO', title='Segregador Simples Nacional', button='OK')