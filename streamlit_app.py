import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
import traceback

# 🔧 Carregar variáveis locais (.env) quando rodar na sua máquina
load_dotenv()

# ⚙️ Configuração da página
st.set_page_config(page_title="Legal AI Agent", page_icon="⚖️")
st.title("⚖️ Legal AI Agent")

# 🔑 Chaves e modelo (Cloud → st.secrets, Local → .env)
api_key = (
    st.secrets.get("OPENROUTER_API_KEY")
    or os.getenv("OPENROUTER_API_KEY")
)
chosen_model = (
    st.secrets.get("DEFAULT_MODEL")
    or os.getenv("DEFAULT_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free")
)
admin_mode = st.secrets.get("ADMIN_MODE") or os.getenv("ADMIN_MODE", "false")

# 🚨 Validar chave
if not api_key:
    st.error("❌ Nenhuma chave encontrada. Configure OPENROUTER_API_KEY.")
    st.stop()

# 🤖 Cliente OpenRouter
client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

# 🧹 Botão para limpar conversa
if st.button("🧹 Limpar conversa"):
    st.session_state.messages = []
    st.rerun()

# 💬 Histórico de conversa
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 📝 Entrada do usuário
if prompt := st.chat_input("Como posso ajudar na sua consulta jurídica?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            with st.spinner("🔎 Consultando o agente jurídico..."):
                stream = client.chat.completions.create(
                    model=chosen_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Você é um assistente jurídico experiente e prestativo. "
                                "Forneça informações legais precisas e concisas, mas sempre oriente o usuário "
                                "a consultar um advogado qualificado para aconselhamento específico."
                            ),
                        }
                    ] + st.session_state.messages,
                    stream=True,
                )

                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)

        except Exception as e:
            st.error(f"⚠️ Ocorreu um erro ao gerar a resposta: {e}")
            print(traceback.format_exc())
            full_response = (
                "⚠️ Desculpe, não consegui processar sua solicitação no momento. Tente novamente mais tarde."
            )
            message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})


    


