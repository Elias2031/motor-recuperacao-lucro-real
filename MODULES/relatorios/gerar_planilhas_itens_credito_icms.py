import pandas as pd  # type: ignore
import os

def gerar_planilha_itens_credito_icms(dados_por_periodo_e_cnpj):
    # os.makedirs('PLANILHAS DE CREDITO ICMS', exist_ok=True)
    os.makedirs('PLANILHAS DE CREDITO PIS COFINS', exist_ok=True)
    os.makedirs('PLANILHAS DE ITENS COMPRADOS', exist_ok=True)
    os.makedirs('PLANILHAS DE CTE QUE GERA CREDITO', exist_ok=True)
    # os.makedirs('SEGREGACAO DE RECEITAS ICMS', exist_ok=True)
    os.makedirs('SEGREGACAO DE RECEITAS PIS COFINS', exist_ok=True)
    os.makedirs('PLANILHAS DE ITENS QUE GERA CREDITO PIS COFINS ICMS ST', exist_ok=True)
    os.makedirs('PLANILHAS DE ITENS A RECUPERAR ICMS', exist_ok=True)

    # Listas para consolidar os dados
    todos_itens_pis_cofins = []
    todos_itens_icms = []

    for periodo, dados_empresa in sorted(dados_por_periodo_e_cnpj.items()):
            razao_social = dados_empresa.get('razao_social', '').replace('/', '_').replace('\\', '_')

            cnpj = dados_empresa['emitente']['cnpj']

            # # --- ICMS ---
            # dataframe_icms = pd.DataFrame(dados_empresa['itens_que_geram_credito_icms'])
            # dataframe_icms.to_excel(
            #     f'PLANILHAS DE CREDITO ICMS/itens_que_geram_credito_icms_{cnpj}_{razao_social}_{periodo}.xlsx',
            #     index=False
            # )
            # for item in dados_empresa['itens_que_geram_credito_icms']:
            #     item_completo = item.copy()
            #     item_completo['CNPJ'] = cnpj
            #     item_completo['Razao Social'] = razao_social
            #     item_completo['Periodo'] = periodo
            #     todos_itens_icms.append(item_completo)

            # --- PIS/COFINS ---
            # dataframe_pis_cofins = pd.DataFrame(dados_empresa['itens_que_geram_credito_pis_cofins'])
            # dataframe_pis_cofins.to_excel(
            #     f'PLANILHAS DE CREDITO PIS COFINS/itens_que_geram_credito_pis_cofins_{cnpj}_{razao_social}_{periodo}.xlsx',
            #     index=False
            # )
            # for item in dados_empresa['itens_que_geram_credito_pis_cofins']:
            #     item_completo = item.copy()
            #     item_completo['CNPJ'] = cnpj
            #     item_completo['Razao Social'] = razao_social
            #     item_completo['Periodo'] = periodo
            #     todos_itens_pis_cofins.append(item_completo)

            # # --- Itens Comprados ---
            # dataframe_itens_entrada = pd.DataFrame(dados_empresa['itens_compras'])
            # dataframe_itens_entrada.to_excel(
            #     f'PLANILHAS DE ITENS COMPRADOS/itens_comprados_{cnpj}_{razao_social}_{periodo}.xlsx',
            #     index=False
            # )
            
            # dataframe_cte_credito = pd.DataFrame(dados_empresa['cte_que_geram_credito'])
            # dataframe_cte_credito.to_excel(
            #     f'PLANILHAS DE CTE QUE GERA CREDITO/CTE_CREDITO_{cnpj}_{razao_social}_{periodo}.xlsx',
            #     index=False
            # )

            # # # --- Segregação ICMS ---
            # # dataframe_icms_itens_segregacao = pd.DataFrame(dados_empresa['itens_segregacao_icms'])
            # # dataframe_icms_itens_segregacao.to_excel(
            # #     f'SEGREGACAO DE RECEITAS ICMS/segregacao_saidas_{cnpj}_{razao_social}_{periodo}.xlsx',
            # #     index=False
            # # )

            # # --- Segregação PIS/COFINS ---
            # dataframe_pis_cofins_itens_segregacao = pd.DataFrame(dados_empresa['itens_segregacao_pis_cofins'])
            # dataframe_pis_cofins_itens_segregacao.to_excel(
            #     f'SEGREGACAO DE RECEITAS PIS COFINS/segregacao_saidas_{cnpj}_{razao_social}_{periodo}.xlsx',
            #     index=False
            # )
            
            # --- Itens Comprados ---
            # dataframe_itens_que_geram_credito_pis_cofins_icms_st= pd.DataFrame(dados_empresa['itens_que_geram_credito_pis_cofins_icms_st'])
            # dataframe_itens_que_geram_credito_pis_cofins_icms_st.to_excel(
            #     f'PLANILHAS DE ITENS QUE GERA CREDITO PIS COFINS ICMS ST/itens_comprados_icms_st_pis_cofins{cnpj}_{razao_social}_{periodo}.xlsx',
            #     index=False
            # )
            
            itens_a_recuperar_icms= pd.DataFrame(dados_empresa['itens_a_recuperar_icms'])
            itens_a_recuperar_icms.to_excel(
                f'PLANILHAS DE ITENS A RECUPERAR ICMS/itens_a_recuperar_icms_{periodo}.xlsx',
                index=False
            )

    # # === Planilha Geral Consolidada - ICMS ===
    # if todos_itens_icms:
    #     df_icms_geral = pd.DataFrame(todos_itens_icms)
    #     df_icms_geral.to_excel(
    #         'PLANILHAS DE CREDITO ICMS/ITENS_GERAIS_CREDITO_ICMS.xlsx',
    #         index=False
    #     )
    #     print("✅ Planilha geral de crédito ICMS gerada com sucesso.")
    # else:
    #     print("⚠️ Nenhum item com crédito de ICMS foi encontrado para consolidar.")

    # === Planilha Geral Consolidada - PIS/COFINS ===
    if todos_itens_pis_cofins:
        df_pis_cofins_geral = pd.DataFrame(todos_itens_pis_cofins)
        df_pis_cofins_geral.to_excel(
            'PLANILHAS DE CREDITO PIS COFINS/ITENS_GERAIS_CREDITO_PIS_COFINS.xlsx',
            index=False
        )
        print("✅ Planilha geral de crédito PIS/COFINS gerada com sucesso.")
    else:
        print("⚠️ Nenhum item com crédito de PIS/COFINS foi encontrado para consolidar.")
