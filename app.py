import os
import datetime
import streamlit as st
import requests
import google.generativeai as genai

st.set_page_config(page_title="Pesquisador Gemini Notebook", page_icon="🔍", layout="wide")

st.title("🔍 Pesquisador de Assuntos Recentes & Gemini")
st.markdown("Busque informações das últimas 36 horas, selecione as fontes e envie para análise do Gemini.")

# --- BARRA LATERAL: Configuração de Chaves de API ---
with st.sidebar:
    st.header("🔑 Configurações de API")
    gemini_api_key = st.text_input("Gemini API Key", type="password", value=st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "")))
    serper_api_key = st.text_input("Serper / News API Key", type="password", help="Usado para buscar notícias recentes nas últimas 36 horas")
    st.info("Insira sua Gemini API Key para executar as análises.")

# --- 1. ENTRADA DO USUÁRIO ---
termo_busca = st.text_input("O que você deseja pesquisar?", placeholder="Ex: eleições 2026, tecnologia...")

def buscar_noticias_36h(query, api_key):
    """Busca notícias/documentos publicados nas últimas 36h."""
    if not api_key:
        return [
            {"title": f"Últimas atualizações sobre {query} - Portal A", "link": "https://noticias.exemplo.com/materia-1", "snippet": "Análise detalhada das movimentações das últimas 24h.", "source": "Portal A"},
            {"title": f"Documento Oficial e Notas sobre {query}", "link": "https://gov.exemplo.br/documento-oficial", "snippet": "Publicação oficial do relatório atualizado.", "source": "Diário Oficial"},
            {"title": f"Análise Especial: Impactos de {query}", "link": "https://analise.exemplo.com/artigo-2", "snippet": "Especialistas discutem os desdobramentos mais recentes.", "source": "Blog de Análise"}
        ]
    
    url = "https://google.serper.dev/news"
    payload = {"q": f"{query} when:36h", "gl": "br", "hl": "pt-br"}
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        results = response.json().get('news', [])
        return [{"title": r.get('title'), "link": r.get('link'), "snippet": r.get('snippet'), "source": r.get('source')} for r in results]
    else:
        st.error("Erro na busca de notícias. Verifique a chave da API de busca.")
        return []

# --- 2. BUSCA E EXIBIÇÃO ---
if st.button("Buscar conteúdos (Últimas 36h)", type="primary"):
    if not termo_busca:
        st.warning("Por favor, digite um assunto para pesquisar.")
    else:
        with st.spinner("Buscando fontes e produções documentais recentes..."):
            st.session_state['resultados'] = buscar_noticias_36h(termo_busca, serper_api_key)
            st.session_state['termo_pesquisado'] = termo_busca

# --- 3. SELEÇÃO COM CHECKBOXES (FLAGS) ---
if 'resultados' in st.session_state and st.session_state['resultados']:
    st.subheader(f"Resultados encontrados para: '{st.session_state['termo_pesquisado']}'")
    st.write("Marque as fontes e produções documentais que deseja analisar:")

    fontes_selecionadas = []
    
    for idx, item in enumerate(st.session_state['resultados']):
        col1, col2 = st.columns([0.05, 0.95])
        with col1:
            marcado = st.checkbox("", key=f"flag_{idx}", value=True)
        with col2:
            st.markdown(f"**[{item['title']}]({item['link']})** - *Fonte: {item['source']}*")
            st.caption(item['snippet'])
            st.write("---")
        
        if marcado:
            fontes_selecionadas.append(item)

    # --- 4. CONEXÃO COM O GEMINI & PROCESSAMENTO ---
    st.subheader("🚀 Processamento e Análise no Gemini")
    
    if fontes_selecionadas:
        st.success(f"{len(fontes_selecionadas)} fonte(s) selecionada(s).")
        
        col_acao1, col_acao2 = st.columns(2)
        with col_acao1:
            modelo_consumo = st.selectbox(
                "Escolha o modelo de consumo da pesquisa:",
                [
                    "Resumo Executivo Geral",
                    "Linha do Tempo dos Fatos",
                    "Análise Crítica e Pontos de Vista",
                    "Perguntas e Respostas (FAQ)",
                    "Roteiro de Apresentação / Briefing"
                ]
            )
            
        with col_acao2:
            st.write(" ")
            st.write(" ")
            enviar_notebook = st.button("Analisar com o Gemini", type="primary")

        if enviar_notebook:
            if not gemini_api_key:
                st.error("Informe a Gemini API Key na barra lateral para continuar.")
            else:
                with st.spinner("Sintetizando fontes e gerando o relatório..."):
                    try:
                        # Configura a chave de API
                        genai.configure(api_key=gemini_api_key)
                        
                        # Concatena as fontes selecionadas como contexto
                        contexto_fontes = "\n\n".join([
                            f"Título: {f['title']}\nFonte: {f['source']}\nLink: {f['link']}\nTrecho: {f['snippet']}"
                            for f in fontes_selecionadas
                        ])
                        
                        prompt_sistema = f"""
                        Você é um assistente de pesquisa especializado.
                        Analise as seguintes fontes sobre '{st.session_state['termo_pesquisado']}' coletadas nas últimas 36 horas:

                        --- FONTES COLETADAS ---
                        {contexto_fontes}
                        --- FIM DAS FONTES ---

                        Elabore uma resposta estruturada seguindo o formato: {modelo_consumo}.
                        Sempre cite as fontes/links fornecidos quando mencionar informações específicas.
                        """
                        
                        # Chama o modelo Gemini 1.5 Flash
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(prompt_sistema)
                        
                        st.balloons()
                        st.subheader(f"📑 Resultado: {modelo_consumo}")
                        st.markdown(response.text)
                        
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao processar com a API do Gemini: {e}")
    else:
        st.warning("Selecione pelo menos uma fonte para continuar.")
