import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from groq import Groq  # api
import uvicorn

app = FastAPI(title="AI Chatbot Backend - Groq Express")

#cors validations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
load_dotenv()

#chave da api groq
GROQ_API_KEY = os.getenv("API_KEY")

# para inicializar cliente da groq
client = Groq(api_key=GROQ_API_KEY)

# modelo llama 3, mais rapido e gratuito
MODELO_GROQ = "llama-3.1-8b-instant"

# para criação do caminho das pastas de personagens e historicos
PASTA_PERSONAGENS = "personagens"
PASTA_HISTORICOS = "historicos"

class ChamadaChat(BaseModel):
    personagem: str
    mensagem_usuario: str
    nome_usuario: str = "Monica"

# ROTA GET Listar personagens
@app.get("/api/personagens")
def listar_personagens():
    if not os.path.exists(PASTA_PERSONAGENS):
        return []
    lista = []
    for arquivo in os.listdir(PASTA_PERSONAGENS):
        if arquivo.endswith(".json"):
            caminho = os.path.join(PASTA_PERSONAGENS, arquivo)
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
                lista.append({
                    "id": arquivo.replace(".json", ""),
                    "nome": dados.get("nome"),
                    "avatar": dados.get("avatar", "images/default.png"),
                    "mensagem_inicial": dados.get("mensagem_inicial", "").replace("{{user}}", "Aisha")
                })
    return lista

# ROTA POST, Chat com velocidade via Groq
@app.post("/api/chat")
def conversar_com_ia(dados: ChamadaChat):
    caminho_json = os.path.join(PASTA_PERSONAGENS, f"{dados.personagem}.json")
    caminho_hist = os.path.join(PASTA_HISTORICOS, f"chat_{dados.personagem}_groq.json")
    
    if not os.path.exists(caminho_json):
        raise HTTPException(status_code=404, detail="Personagem não encontrado.")

    with open(caminho_json, "r", encoding="utf-8") as f:
        char_data = json.load(f)
    
    instrucao_sistema = char_data["descricao_longa"].replace("{{user}}", dados.nome_usuario).replace("{{char}}", char_data["nome"])

    os.makedirs(PASTA_HISTORICOS, exist_ok=True)
    if os.path.exists(caminho_hist):
        with open(caminho_hist, "r", encoding="utf-8") as f:
            historico = json.load(f)
    else:
        historico = [{"role": "system", "content": instrucao_sistema}]

    # Adiciona a nova mensagem do usuário no histórico completo
    historico.append({"role": "user", "content": dados.mensagem_usuario})

    # Função geradora para ler a resposta da Groq em tempo real
    def gerador_de_resposta():
        texto_completo = ""
        try:
            
            # Isolando a instrução secreta do sistema
            mensagem_sistema = [msg for msg in historico if msg["role"] == "system"]
            # Isoladas todas as conversas trocadas (User e Assistant)
            mensagens_conversa = [msg for msg in historico if msg["role"] != "system"]
            
            # cortada para enviar apenas as últimas 60 mensagens de chat
            ultimas_mensagens = mensagens_conversa[-60:]
            
            # Juntado o sistema com o bloco enxuto de mensagens
            historico_resumido = mensagem_sistema + ultimas_mensagens
            

            # Chamada de streaming para a Groq Cloud 
            resposta_stream = client.chat.completions.create(
                model=MODELO_GROQ,
                messages=historico_resumido,  # 
                stream=True,
            )
            
            for chunk in resposta_stream:
                # Captura o pedaço de texto se ele existir no chunk atual
                pedaco_texto = chunk.choices[0].delta.content
                if pedaco_texto:
                    texto_completo += pedaco_texto
                    yield pedaco_texto
            
            # Salva no histórico completo
            historico.append({"role": "assistant", "content": texto_completo})
            with open(caminho_hist, "w", encoding="utf-8") as f:
                json.dump(historico, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            yield f"\n[Erro no servidor Groq: {e}]"

    return StreamingResponse(gerador_de_resposta(), media_type="text/plain")
#get para historico
@app.get("/api/historico/{personagem}")
def obter_historico(personagem:str):
    #montanado caminho para a pasta historicos
    caminho_hist = os.path.join(PASTA_HISTORICOS, f"chat_{personagem}_groq.json")

    #verifica se o arquivo existe, le e devolve as mensagens salvas
    if os.path.exists(caminho_hist):
        with open(caminho_hist, "r", encoding="utf-8") as f:
             return json.load(f) #retorna o json das mensagens

    #retorna lista vazia se não existir historico ainda
    return[]
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    