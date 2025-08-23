from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
from dotenv import load_dotenv
import os
import re

# Carrega as variáveis do arquivo .env
load_dotenv()

# Inicializa clientes
client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = Flask(__name__)

# Estado simples por usuário
usuarios = {}

# ====== Configurações da Escola ======
ESCOLA_NOME = "Escola de Futebol Nunes 9"
WHATS_ATENDENTE = "(21) 98943-9693"
MENSALIDADE = 160.00
HORARIOS = [
    "08h30 às 10h30",
    "15h00 às 17h00",
    "17h00 às 19h00",
]
# =====================================

def menu_texto():
    return (
        f"🏆 {ESCOLA_NOME} – Matrículas Abertas! ⚽\n\n"
        "Olá! 👋 Selecione uma opção para continuar:\n"
        "1️⃣ Informações sobre as aulas\n"
        "2️⃣ Documentos necessários para matrícula\n"
        "3️⃣ Valores e formas de pagamento\n"
        "4️⃣ Horários de treino\n"
        "5️⃣ Falar com um atendente\n\n"
        "Digite o número da opção ou escreva *menu* para ver as opções novamente."
    )

def responder_opcao(opcao: str) -> str:
    opcao = opcao.strip()

    if opcao == "1":
        return (
            "⚽ *Informações sobre as aulas*\n\n"
            "Os treinos acontecem de *segunda a quinta-feira*.\n"
            "Cada aluno treina *3 vezes por semana*.\n"
            "Faixa etária: *crianças de 5 a 12 anos*."
        )

    elif opcao == "2":
        return (
            "📄 *Documentos necessários para matrícula*\n\n"
            "- 1 foto 3x4\n"
            "- Cópia do RG ou Certidão de Nascimento\n"
            "- Cópia do CPF\n"
            "- Comprovante de residência\n"
            "- RG e CPF do responsável\n"
            "- Declaração escolar\n"
            "- Atestado médico\n"
            "_Todas as cópias devem ser legíveis._"
        )

    elif opcao == "3":
        return (
            "💰 *Valores e formas de pagamento*\n\n"
            f"A mensalidade é de *R$ {MENSALIDADE:.2f}*.\n"
            "Aceitamos dinheiro, Pix ou transferência."
        )

    elif opcao == "4":
        return (
            "⏰ *Horários de treino* (segunda a quinta-feira)\n\n"
            f"• {HORARIOS[0]}\n"
            f"• {HORARIOS[1]}\n"
            f"• {HORARIOS[2]}"
        )

    elif opcao == "5":
        return (
            "📲 *Falar com um atendente*\n\n"
            f"Chame no WhatsApp: {WHATS_ATENDENTE}\n"
            "Se preferir, responda aqui que encaminhamos ao responsável. 🙂"
        )

    return ""  # sem correspondência; deixa o fluxo tratar

def responder_com_chatgpt(mensagem_usuario):
    # Prompt do atendente com as informações fixas da escola
    sistema = (
        "Você é um atendente simpático e objetivo da 'Escola de Futebol Nunes 9'. "
        "Use sempre português claro e acolhedor. "
        "Se o usuário pedir algo do menu, incentive a digitar um número (1 a 5) ou 'menu'. "
        "Use as informações OFICIAIS abaixo ao responder dúvidas:\n\n"
        f"- Nome: {ESCOLA_NOME}\n"
        "- Público: crianças de 5 a 12 anos\n"
        "- Treinos: de segunda a quinta-feira; 3 vezes por semana por aluno\n"
        f"- Horários: {', '.join(HORARIOS)}\n"
        f"- Mensalidade: R$ {MENSALIDADE:.2f}\n"
        f"- Contato do atendente: {WHATS_ATENDENTE}\n"
        "- Documentos: 1 foto 3x4; RG ou Certidão de Nascimento; CPF; "
        "comprovante de residência; RG e CPF do responsável; declaração escolar; atestado médico; "
        "todas as cópias devem ser legíveis.\n"
    )

    resposta = client_openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": sistema},
            {"role": "user", "content": mensagem_usuario}
        ]
    )
    return resposta.choices[0].message.content.strip()

@app.route('/whatsapp', methods=['POST'])
def whatsapp():
    numero = request.form.get('From')
    mensagem = (request.form.get('Body') or "").strip()
    resp = MessagingResponse()

    # Normaliza apenas dígitos quando usuário enviar algo como "Opção 1"
    somente_numero = re.sub(r"\D", "", mensagem)

    # Primeira interação ou pedido de menu
    if numero not in usuarios or mensagem.lower() in {"menu", "opções", "opcoes"}:
        usuarios[numero] = {"estado": "menu"}
        resp.message(menu_texto())
        return str(resp)

    # Se usuário digitou 1–5, responde direto
    if somente_numero in {"1", "2", "3", "4", "5"}:
        resposta = responder_opcao(somente_numero)
        if resposta:
            resp.message(resposta + "\n\nDigite *menu* para voltar às opções.")
            return str(resp)

    # Caso contrário, usa ChatGPT como fallback
    resposta_gpt = responder_com_chatgpt(mensagem)
    resp.message(resposta_gpt + "\n\nSe preferir, digite *menu* para ver as opções.")
    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)
