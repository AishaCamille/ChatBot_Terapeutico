import os
import json
import streamlit as st
import ollama

# Configuração da página do navegador
st.set_page_config(page_title="Oficina do James - LOCAL", page_icon="🔧", layout="centered")

NOME_DO_USUARIO = "Aisha"
personagem_atual = "Soleil"
MODELO_LOCAL = "llama3" # modelo utilizado

caminho_json = f"backend/personagens/{personagem_atual}.json"
# arquvivo do historico do personagem
caminho_historico = f"backend/historicos/chat_{personagem_atual}_local.json"

# Botão na Barra Lateral para resetar o chat
with st.sidebar:
    st.header("⚙️ Controle do Bot")
    if st.button("♻️ Reiniciar Chat do Zero"):
        if "local_messages" in st.session_state: 
            del st.session_state.local_messages
        if os.path.exists(caminho_historico):
            os.remove(caminho_historico)
        st.rerun()

# Carrega a ficha técnica do Personagem
@st.cache_data
def carregar_personagem(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

try:
    char_data = carregar_personagem(caminho_json)
except FileNotFoundError:
    st.error(f"Arquivo do personagem não encontrado em {caminho_json}")
    st.stop()

instrucao_sistema = char_data["descricao_longa"].replace("{{user}}", NOME_DO_USUARIO).replace("{{char}}", char_data["nome"])
mensagem_inicial = char_data["mensagem_inicial"].replace("{{user}}", NOME_DO_USUARIO).replace("{{char}}", char_data["nome"])

# Gerenciamento do Histórico Local (Formato Padrão de Mercado)
if "local_messages" not in st.session_state:
    if os.path.exists(caminho_historico):
        with open(caminho_historico, "r", encoding="utf-8") as f:
            st.session_state.local_messages = json.load(f)
    else:
        # No Ollama, a instrução do sistema entra como a primeira mensagem do histórico
        st.session_state.local_messages = [
            {"role": "system", "content": instrucao_sistema}
        ]

# Interface Visual
st.title(f"🔧 Oficina do {char_data['nome']} (Offline & Ilimitado)")
st.caption("Sem APIs, sem limites de cota, rodando direto no seu hardware.")
st.markdown("---")

# Renderiza as mensagens na tela (ignorando o prompt de sistema oculto)
if len(st.session_state.local_messages) == 1:
    with st.chat_message("assistant", avatar="👨‍🔧"):
        st.markdown(mensagem_inicial)
else:
    for msg in st.session_state.local_messages:
        if msg["role"] == "system":
            continue
        role_visual = "user" if msg["role"] == "user" else "assistant"
        avatar_visual = "👤" if role_visual == "user" else "👨‍🔧"
        with st.chat_message(role_visual, avatar=avatar_visual):
            st.markdown(msg["content"])

# Caixa de Entrada do Chat
placeholderdinamico= f"Diga algo para {personagem_atual}..."
if user_input := st.chat_input(placeholderdinamico):
    
    # Exibe sua fala na tela
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    
    # Adiciona ao histórico da sessão
    st.session_state.local_messages.append({"role": "user", "content": user_input})

    # Resposta do James via Ollama Local com Streaming
    with st.chat_message("assistant", avatar="👨‍🔧"):
        placeholder_resposta = st.empty()
        texto_completo_ia = ""
        
        # Dispara a requisição para o servidor do Ollama no seu PC
        resposta_stream = ollama.chat(
            model=MODELO_LOCAL,
            messages=st.session_state.local_messages,
            stream=True
        )
        
        for chunk in resposta_stream:
            texto_completo_ia += chunk['message']['content']
            placeholder_resposta.markdown(texto_completo_ia + "▌")
        
        placeholder_resposta.markdown(texto_completo_ia)

    # Salva a resposta da IA no histórico
    st.session_state.local_messages.append({"role": "assistant", "content": texto_completo_ia})

    # Grava as alterações no arquivo de histórico local
    with open(caminho_historico, "w", encoding="utf-8") as f:
        json.dump(st.session_state.local_messages, f, ensure_ascii=False, indent=2)