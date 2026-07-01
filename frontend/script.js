
async function nomePerso() {
        const select = document.getElementById("select-personagem");//qual personagem
        const titulo = document.getElementById("titulo");
        const nomeSelect = select.options[select.selectedIndex].text;//pegar o texto que foi clicado
        titulo.innerHTML = `<h1 class="Nome">${nomeSelect}</h1>`; //escreve no topo da tela
    
}


async function historico_banco(){
    nomePerso();
 //personagem selecionado do front
    const select = document.getElementById("select-personagem");//qual personagem
    const chatDiv = document.getElementById("chat"); //onde vai ficar o chat
    const personagemEscolhido = select.value;

    //limpar tela do char para não acumular chat de outros personagens
    chatDiv.innerHTML = "";

    //pedido do histprico para o backend
    const response = await fetch(`http://127.0.0.1:8000/api/historico/${personagemEscolhido}`)
    const historico = await response.json();

    //passa por cada mensagem salva no historico e manda para a tela
    historico.forEach(msg =>{
        //mensagem secreta do sistema ignorada
        if(msg.role === "system") return;

        //define se a classe css escolhida é do user ou do bot
        const classeVisual = msg.role === "user" ? "user" : "bot";
        const nomeExibido = msg.role === "user" ? "Voce" : personagemEscolhido;

        //balãozinho de texto na tela
        chatDiv.innerHTML += `<div class="${classeVisual}"><b>${nomeExibido}:</b> ${msg.content}</div>`;
    });
    //scroll descer ate o final
    chatDiv.scrollTop= chatDiv.scrollHeight;
}

async function enviarParaOBackend(event) {
    if (event) event.preventDefault();
    const input = document.getElementById("input-mensagem");
    const select = document.getElementById("select-personagem");
    const chatDiv = document.getElementById("chat");

    const textoUsuario = input.value;
    const personagemEscolhido = select.value;

    if (!textoUsuario.trim()) return; // Não envia se estiver vazio

    // 1. Mostra a sua mensagem na tela
    chatDiv.innerHTML += `<div class="user"><b>Você:</b> ${textoUsuario}</div>`;
    input.value = ""; // Limpa o campo de texto

    // 2. Cria um balãozinho vazio para a IA preencher palavra por palavra
    const botMsgDiv = document.createElement("div");
    botMsgDiv.className = "bot";
    botMsgDiv.innerHTML = `<b>${personagemEscolhido}:</b> <span class="texto-ia"></span>`;
    chatDiv.appendChild(botMsgDiv);
    
    const spanTextoIA = botMsgDiv.querySelector(".texto-ia");

    // 3. Faz a conexão real com o seu FastAPI (Back-end)
    const response = await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            personagem: personagemEscolhido,
            mensagem_usuario: textoUsuario,
            nome_usuario: "Monica" // Seu nome configurado
        })
    });

    // 4. Mecanismo de STREAMING: Lê a resposta palavra por palavra
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    while (true) {
        const { value, done } = await reader.read();
        if (done) break; // Quando o backend parar de mandar texto, o loop acaba

        // Transforma o pedaço de dados binários em texto normal
        const pedacoTexto = decoder.decode(value);
        
        // Adiciona esse pedacinho na tela imediatamente
        spanTextoIA.innerText += pedacoTexto;

        // Faz o scroll do chat descer automaticamente junto com o texto
        chatDiv.scrollTop = chatDiv.scrollHeight;
    }
    input.focus();
}

//mensagem abrir assim que a pag carrear
window.onload = () => {
    historico_banco();
};