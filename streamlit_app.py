import streamlit as st
import os
import io
import re
import traceback
import json
import importlib
from dotenv import load_dotenv
from fpdf import FPDF
from docx import Document

_REQUIRED = {"openai": "openai>=1.3"}
_missing = []
for mod, pip_name in _REQUIRED.items():
    if importlib.util.find_spec(mod) is None:
        _missing.append(pip_name)
if _missing:
    st.error(f"Pacotes ausentes: {', '.join(_missing)}. Execute: pip install -r requirements.txt")
    st.stop()

from openai import OpenAI
from agente import classificar_acao


# 🔧 Carregar variáveis locais (.env) com prioridade sobre variáveis antigas da sessão
load_dotenv(override=True)

# ⚙️ Configuração da página
st.set_page_config(
    page_title="Legal AI Agent | High-Fidelity UI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CARREGAR RECURSOS EXTERNOS (DESIGN & LOCALIZAÇÃO) ---
def load_translations(lang_code):
    try:
        with open(f"locales/{lang_code}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        try:
            with open("locales/pt.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

def load_css():
    try:
        with open("assets/css/style.css", "r", encoding="utf-8") as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar CSS: {e}")

# Carregar estilos globais
load_css()

# Inicializar estados de sessão importantes
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "chat"

# 🔑 Provedor e modelo (Groq tem prioridade, seguido por Ollama Cloud e Hugging Face)
groq_api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
ollama_api_key = os.getenv("OLLAMA_API_KEY") or st.secrets.get("OLLAMA_API_KEY")
hf_token = os.getenv("HF_TOKEN") or st.secrets.get("HF_TOKEN")

if groq_api_key:
    provider_name = "Groq"
    chosen_model = os.getenv("GROQ_MODEL") or st.secrets.get("GROQ_MODEL") or "openai/gpt-oss-120b"
    client = OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
elif ollama_api_key:
    provider_name = "Ollama Cloud"
    chosen_model = os.getenv("OLLAMA_MODEL") or st.secrets.get("OLLAMA_MODEL") or "deepseek-v4.1-flash"
    client = OpenAI(api_key=ollama_api_key, base_url="https://ollama.com/v1")
elif hf_token:
    provider_name = "Hugging Face"
    chosen_model = os.getenv("DEFAULT_MODEL") or st.secrets.get("DEFAULT_MODEL") or "openai/gpt-oss-120b:fastest"
    client = OpenAI(api_key=hf_token, base_url="https://router.huggingface.co/v1")
else:
    provider_name = "Ollama Cloud"
    chosen_model = os.getenv("OLLAMA_MODEL") or st.secrets.get("OLLAMA_MODEL") or "deepseek-v4.1-flash"
    client = None

has_api_key = client is not None


def show_api_error(context, error):
    status_code = getattr(error, "status_code", None)
    if status_code == 402:
        details = f"{provider_name} informou que há uma exigência de créditos ou faturamento para este modelo."
    elif status_code in (401, 403):
        credential = {
            "Groq": "GROQ_API_KEY",
            "Ollama Cloud": "OLLAMA_API_KEY",
            "Hugging Face": "HF_TOKEN",
        }[provider_name]
        details = f"Verifique se {credential} está válido e tem acesso ao serviço."
    elif status_code == 404:
        details = f"O modelo '{chosen_model}' não foi encontrado ou não está disponível para sua conta."
    else:
        details = str(error)
    st.error(f"{context}: {details}")




# --- SIDEBAR E ESTRUTURA DE MARCA (LOGO SVG) ---
with st.sidebar:
    # Renderizar logotipo vetorial premium em SVG
    st.markdown("""
    <div class="logo-container">
        <svg viewBox="0 0 100 100" width="70" height="70" xmlns="http://www.w3.org/2000/svg">
            <!-- Central pillar -->
            <line x1="50" y1="20" x2="50" y2="80" stroke="#4A90E2" stroke-width="4" stroke-linecap="round"/>
            <!-- Base -->
            <path d="M 30 80 Q 50 75 70 80 L 75 83 L 25 83 Z" fill="#4A90E2"/>
            <!-- Crossbeam -->
            <line x1="25" y1="35" x2="75" y2="35" stroke="#4A90E2" stroke-width="3" stroke-linecap="round"/>
            <!-- Left Scale Thread & Pan -->
            <line x1="25" y1="35" x2="25" y2="55" stroke="#4A90E2" stroke-width="1.5" stroke-dasharray="2,2"/>
            <path d="M 15 55 L 35 55 Q 25 65 15 55 Z" fill="#E2E8F0" stroke="#4A90E2" stroke-width="2"/>
            <circle cx="20" cy="50" r="3" fill="#3B82F6"/>
            <circle cx="30" cy="50" r="3" fill="#10B981"/>
            <circle cx="25" cy="44" r="4" fill="#6366F1"/>
            <line x1="20" y1="50" x2="25" y2="44" stroke="#4A90E2" stroke-width="1"/>
            <line x1="30" y1="50" x2="25" y2="44" stroke="#4A90E2" stroke-width="1"/>
            <!-- Right Scale Thread & Pan -->
            <line x1="75" y1="35" x2="75" y2="55" stroke="#4A90E2" stroke-width="1.5" stroke-dasharray="2,2"/>
            <path d="M 65 55 L 85 55 Q 75 65 65 55 Z" fill="#E2E8F0" stroke="#4A90E2" stroke-width="2"/>
            <circle cx="70" cy="50" r="3" fill="#3B82F6"/>
            <circle cx="80" cy="50" r="3" fill="#10B981"/>
            <circle cx="75" cy="44" r="4" fill="#6366F1"/>
            <line x1="70" y1="50" x2="75" y2="44" stroke="#4A90E2" stroke-width="1"/>
            <line x1="80" y1="50" x2="75" y2="44" stroke="#4A90E2" stroke-width="1"/>
            <!-- Glowing central node representing AI -->
            <circle cx="50" cy="20" r="6" fill="#4A90E2" style="filter: drop-shadow(0 0 5px rgba(74,144,226,0.6));"/>
            <circle cx="50" cy="20" r="3" fill="#FFFFFF"/>
        </svg>
        <div class="logo-title" style="font-size:1.25rem;">LEGAL AI AGENT</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Seletor de Idioma Profissional com Bandeiras
    lang_option = st.selectbox(
        "🌐 Language / Idioma / Langue",
        options=["Português 🇧🇷", "English 🇺🇸", "Français 🇫🇷"],
        index=0
    )
    
    lang_map = {
        "Português 🇧🇷": "pt",
        "English 🇺🇸": "en",
        "Français 🇫🇷": "fr"
    }
    lang = lang_map[lang_option]
    t = load_translations(lang)
    
    # Renderizar legenda localizada do logotipo
    st.markdown(f"""
    <div style="text-align:center; margin-top:-10px; margin-bottom:20px;">
        <span class="logo-subtitle">{t["subtitle"]}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção de Navegação Estilizada (SaaS style)
    st.markdown(f"<p style='font-size:0.75rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:10px;'>{t['menu_header']}</p>", unsafe_allow_html=True)
    
    chat_type = "primary" if st.session_state.current_page == "chat" else "secondary"
    docs_type = "primary" if st.session_state.current_page == "docs" else "secondary"
    juris_type = "primary" if st.session_state.current_page == "juris" else "secondary"
    
    if st.button(t["menu_chat"], use_container_width=True, type=chat_type, key="nav_chat"):
        st.session_state.current_page = "chat"
        st.rerun()
        
    if st.button(t["menu_docs"], use_container_width=True, type=docs_type, key="nav_docs"):
        st.session_state.current_page = "docs"
        st.rerun()
        
    if st.button(t["menu_juris"], use_container_width=True, type=juris_type, key="nav_juris"):
        st.session_state.current_page = "juris"
        st.rerun()

    
    st.divider()
    
    # Painel de Métricas Rápidas (Dashboard Style)
    st.markdown(f"<p style='font-size:0.75rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:10px;'>{t['metrics_header']}</p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style="background:rgba(10,25,47,0.6); border:1px solid rgba(74,144,226,0.2); padding:10px 5px; border-radius:8px; text-align:center; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
            <div style="font-size:0.65rem; color:#8892B0; text-transform:uppercase; font-weight:600;">{t['metric_time_lbl']}</div>
            <div style="font-size:1.05rem; font-weight:700; color:#4A90E2; font-family:'Outfit',sans-serif; margin-top:2px;">&lt; 1.2s</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background:rgba(10,25,47,0.6); border:1px solid rgba(74,144,226,0.2); padding:10px 5px; border-radius:8px; text-align:center; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
            <div style="font-size:0.65rem; color:#8892B0; text-transform:uppercase; font-weight:600;">{t['metric_precision_lbl']}</div>
            <div style="font-size:1.05rem; font-weight:700; color:#10B981; font-family:'Outfit',sans-serif; margin-top:2px;">98.4%</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    
    # Status e Ações
    st.markdown(f"<p style='font-size:0.75rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:10px;'>{t['sys_header']}</p>", unsafe_allow_html=True)
    st.caption(f"{provider_name} · {t['sys_model']} \n`{chosen_model.split('/')[-1]}`")
    
    pulse_color = "#10B981" if has_api_key else "#EF4444"
    status_label = t['sys_status_online'] if has_api_key else 'Aguardando Chave'
    
    st.markdown(f"""
    <div style="display:flex; align-items:center; margin-top:10px; font-size:0.8rem; color:#8892B0;">
        <span class="status-pulse" style="background-color: {pulse_color}; box-shadow: 0 0 0 0 {pulse_color}aa;"></span> {status_label}
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    if st.button(t["clear_btn"], use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.rerun()

# --- FUNÇÕES DE RENDERIZAÇÃO DAS PÁGINAS ---

def render_chat_page(t):
    # Header principal elegante em Glassmorphism
    st.markdown(f"""
    <div style="background-color: rgba(23, 42, 69, 0.75); backdrop-filter: blur(8px); padding: 25px; border-radius: 12px; border: 1px solid rgba(74, 144, 226, 0.25); margin-bottom: 25px; box-shadow: 0 8px 16px -1px rgba(0, 0, 0, 0.25);">
        <h1 style="margin:0; font-size:2.2rem; color:#E6F1FF !important; text-shadow: 0 0 15px rgba(74,144,226,0.1);">{t['page_title']}</h1>
        <p style="margin:5px 0 0 0; color:#8892B0; font-size:1.05rem;">
            {t['page_desc']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Exibir histórico de conversa com badges de classificação inteligente
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "user" and "category" in message and message["category"] != "desconhecido":
                badge_color = "#4A90E2" if message["category"] == "civil" else ("#10B981" if message["category"] == "trabalhista" else "#EF4444")
                st.markdown(f'<div style="margin-top: 5px;"><span style="background-color:{badge_color}22; color:{badge_color}; border: 1px solid {badge_color}44; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; font-family:\'Outfit\',sans-serif; letter-spacing:0.5px;">⚖️ {message["category"]}</span></div>', unsafe_allow_html=True)

    # Entrada de chat
    chat_prompt = st.chat_input(t["input_placeholder"])
    final_prompt = chat_prompt if chat_prompt else None

    # Lógica de envio e processamento do prompt
    if final_prompt:
        # Classificação inteligente baseada na lógica local do agente.py
        categoria = classificar_acao(final_prompt)
        
        # Inserir categoria no histórico de mensagens
        st.session_state.messages.append({"role": "user", "content": final_prompt, "category": categoria})
        
        with st.chat_message("user"):
            st.markdown(final_prompt)
            if categoria != "desconhecido":
                badge_color = "#4A90E2" if categoria == "civil" else ("#10B981" if categoria == "trabalhista" else "#EF4444")
                st.markdown(f'<div style="margin-top: 5px;"><span style="background-color:{badge_color}22; color:{badge_color}; border: 1px solid {badge_color}44; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; font-family:\'Outfit\',sans-serif; letter-spacing:0.5px;">⚖️ {categoria}</span></div>', unsafe_allow_html=True)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            # Customizar a instrução do sistema dinamicamente com base na intenção do usuário
            system_instruction = t["system_prompt"]
            if categoria == "trabalhista":
                system_instruction += " Foco especial em Legislação Trabalhista (CLT), verbas rescisórias, FGTS, férias e direitos de emprego."
            elif categoria == "civil":
                system_instruction += " Foco especial em Código Civil brasileiro, obrigações, contratos, indenizações e direito de família/heranças."
            elif categoria == "penal":
                system_instruction += " Foco especial em Código Penal e Processo Penal brasileiro, garantias fundamentais, tipicidade e penas."

            # Preparar o histórico limpando metadados internos de dicionários antes de enviar ao modelo
            llm_messages = [{"role": "system", "content": system_instruction}]
            for msg in st.session_state.messages:
                llm_messages.append({"role": msg["role"], "content": msg["content"]})

            try:
                with st.spinner(t["spinner_msg"]):
                    stream = client.chat.completions.create(
                        model=chosen_model,
                        messages=llm_messages,
                        stream=True,
                    )

                    for chunk in stream:
                        choices = getattr(chunk, "choices", None) or []
                        if not choices:
                            continue

                        delta = getattr(choices[0], "delta", None)
                        content = getattr(delta, "content", None) if delta else None
                        if content:
                            full_response += content
                            message_placeholder.markdown(full_response + "▌")

                if full_response:
                    message_placeholder.markdown(full_response)
                else:
                    full_response = t["no_response"]
                    message_placeholder.markdown(full_response)

            except Exception as e:
                show_api_error(t["error_msg"], e)
                full_response = t["error_generic"]
                message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.rerun()


def render_docs_page(t):
    st.markdown("""
    <div style="background-color: rgba(23, 42, 69, 0.75); backdrop-filter: blur(8px); padding: 25px; border-radius: 12px; border: 1px solid rgba(74, 144, 226, 0.25); margin-bottom: 25px; box-shadow: 0 8px 16px -1px rgba(0, 0, 0, 0.25);">
        <h1 style="margin:0; font-size:2.2rem; color:#E6F1FF !important; text-shadow: 0 0 15px rgba(74,144,226,0.1);">📜 Gerador de Documentos Jurídicos</h1>
        <p style="margin:5px 0 0 0; color:#8892B0; font-size:1.05rem;">
            Redija minutas formais de contratos, procurações ou petições iniciais padronizadas de acordo com o direito brasileiro.
        </p>
    </div>
    """, unsafe_allow_html=True)

    doc_type = st.selectbox(
        "Tipo de Documento Jurídico",
        options=["Contrato de Prestação de Serviços", "Procuração Ad Judicia", "Notificação Extrajudicial", "Petição Inicial Simplificada"],
        index=0
    )

    col1, col2 = st.columns(2)
    with col1:
        outorgante = st.text_input("Nome do Contratante / Outorgante", placeholder="Ex: João da Silva")
        outorgante_doc = st.text_input("CPF / CNPJ do Contratante", placeholder="Ex: 000.000.000-00")
        outorgante_addr = st.text_input("Endereço do Contratante", placeholder="Ex: Rua das Flores, 123 - Centro")
    with col2:
        outorgado = st.text_input("Nome do Contratado / Outorgado", placeholder="Ex: Dra. Patrícia Medeiros (Advogada)")
        outorgado_doc = st.text_input("CPF / CNPJ / OAB do Contratado", placeholder="Ex: OAB/SP 123.456")
        outorgado_addr = st.text_input("Endereço do Contratado", placeholder="Ex: Av. Paulista, 1000 - Bela Vista")

    detalhes = st.text_area("Detalhes específicos e cláusulas acordadas", 
                            placeholder="Ex: Contrato de prestação de serviço de consultoria em TI com vigência de 12 meses, valor mensal de R$ 3.000,00 reajustável pelo IPCA, com multa de 10% em caso de rescisão sem aviso prévio.")

    if st.button("Gerar Minuta Profissional", use_container_width=True, type="primary"):
        if not outorgante or not outorgado:
            st.warning("⚠️ Insira o nome das partes envolvidas antes de gerar o documento.")
        else:
            with st.spinner("✍️ Redigindo e revisando a minuta com rigor formal..."):
                prompt = (
                    f"Aja como um advogado experiente especializado em redação de minutas jurídicas brasileiras. "
                    f"Elabore uma minuta formal e juridicamente válida de {doc_type} com base nos dados fornecidos abaixo:\n"
                    f"- Contratante / Outorgante: {outorgante}, CPF/CNPJ: {outorgante_doc}, Endereço: {outorgante_addr}\n"
                    f"- Contratado / Outorgado: {outorgado}, Doc/OAB: {outorgado_doc}, Endereço: {outorgado_addr}\n"
                    f"- Detalhes do Acordo: {detalhes}\n\n"
                    f"Estruture o documento formalmente com títulos, cláusulas bem definidas e espaço para assinaturas ao final. "
                    f"Forneça apenas o documento jurídico sem notas explicativas iniciais ou finais."
                )
                try:
                    response = client.chat.completions.create(
                        model=chosen_model,
                        messages=[
                            {"role": "system", "content": "Você é um assistente sênior especializado em redação de minutas contratuais e peças no direito brasileiro. Utilize linguagem formal e precisa."},
                            {"role": "user", "content": prompt}
                        ],
                        stream=False
                    )
                    doc_content = response.choices[0].message.content
                    st.session_state.last_generated_doc = doc_content
                except Exception as e:
                    show_api_error("Erro ao gerar o documento", e)

    if "last_generated_doc" in st.session_state:
        st.divider()
        st.subheader("Minuta Gerada")
        st.markdown(f"""
        <div style="background-color: rgba(10, 25, 47, 0.55); border: 1px solid rgba(74, 144, 226, 0.25); padding: 25px; border-radius: 10px; font-family: monospace; white-space: pre-wrap; color: #E6F1FF; box-shadow: 0 4px 12px rgba(0,0,0,0.25);">
{st.session_state.last_generated_doc}
        </div>
        """, unsafe_allow_html=True)

        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            st.download_button(
                label="📥 Baixar .txt",
                data=st.session_state.last_generated_doc,
                file_name=f"minuta_{doc_type.lower().replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col_btn2:
            # Geração de PDF
            def create_pdf(text):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Helvetica", size=12)
                # Substituir caracteres não suportados pelo FPDF básico
                clean_text = text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, text=clean_text)
                return bytes(pdf.output())

            st.download_button(
                label="📄 Baixar .pdf",
                data=create_pdf(st.session_state.last_generated_doc),
                file_name=f"minuta_{doc_type.lower().replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with col_btn3:
            # Geração de DOCX
            def create_docx(text):
                doc = Document()
                doc.add_paragraph(text)
                buffer = io.BytesIO()
                doc.save(buffer)
                return buffer.getvalue()

            st.download_button(
                label="📝 Baixar .docx",
                data=create_docx(st.session_state.last_generated_doc),
                file_name=f"minuta_{doc_type.lower().replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

        st.write("")
        if st.button("🧹 Limpar Documento", use_container_width=True):
            del st.session_state.last_generated_doc
            st.rerun()


def render_juris_page(t):
    st.markdown("""
    <div style="background-color: rgba(23, 42, 69, 0.75); backdrop-filter: blur(8px); padding: 25px; border-radius: 12px; border: 1px solid rgba(74, 144, 226, 0.25); margin-bottom: 25px; box-shadow: 0 8px 16px -1px rgba(0, 0, 0, 0.25);">
        <h1 style="margin:0; font-size:2.2rem; color:#E6F1FF !important; text-shadow: 0 0 15px rgba(74,144,226,0.1);">🛡️ Consulta de Jurisprudência & Precedentes</h1>
        <p style="margin:5px 0 0 0; color:#8892B0; font-size:1.05rem;">
            Descreva seu caso para receber uma análise de possíveis teses e linhas jurisprudenciais. A ferramenta não consulta bases oficiais; confirme qualquer precedente em fonte confiável.
        </p>
    </div>
    """, unsafe_allow_html=True)

    caso_fatico = st.text_area(
        "Fatos do Caso Concreto", 
        placeholder="Ex: Passageiro teve voo nacional cancelado sem aviso prévio pela companhia aérea, acarretando na perda de um compromisso de trabalho importante no dia seguinte."
    )

    if st.button("Pesquisar Precedentes", use_container_width=True, type="primary"):
        if not caso_fatico:
            st.warning("⚠️ Insira a descrição dos fatos para realizarmos a pesquisa jurisprudencial.")
        else:
            with st.spinner("🔎 Analisando possíveis teses jurídicas..."):
                prompt = (
                    f"Aja como um analista jurídico especializado. Com base na situação fática abaixo, identifique possíveis teses jurídicas "
                    f"e linhas jurisprudenciais relevantes no direito brasileiro, com uma análise estimada de aplicabilidade. "
                    f"Não invente números de processos, ementas, datas ou decisões; não afirme ter consultado tribunais. "
                    f"Se não puder identificar um precedente com segurança, descreva apenas a tese e recomende pesquisa em fonte oficial.\n\n"
                    f"Situação Fática: {caso_fatico}\n\n"
                    f"Formate o resultado de maneira muito estruturada e profissional utilizando Markdown."
                )
                try:
                    response = client.chat.completions.create(
                        model=chosen_model,
                        messages=[
                            {"role": "system", "content": "Você é um assistente de análise jurídica brasileira. Nunca invente precedentes, números de processos ou ementas. Deixe claro que sua análise não substitui consulta a bases oficiais nem aconselhamento de advogado."},
                            {"role": "user", "content": prompt}
                        ],
                        stream=False
                    )
                    juris_result = response.choices[0].message.content
                    st.session_state.last_juris_search = juris_result
                except Exception as e:
                    show_api_error("Erro ao analisar precedentes", e)

    if "last_juris_search" in st.session_state:
        st.divider()
        st.subheader("Precedentes Encontrados & Análise de Aplicabilidade")
        st.markdown(st.session_state.last_juris_search)
        if st.button("🧹 Limpar Resultados", use_container_width=True):
            del st.session_state.last_juris_search
            st.rerun()


# --- DIRECIONADOR DE PÁGINAS (ROTEADOR PRINCIPAL) ---
if not has_api_key:
    st.markdown("""
    <div style="background-color: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.35); padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(239, 68, 68, 0.05); backdrop-filter: blur(8px);">
        <h3 style="margin:0; font-size:1.4rem; color:#EF4444 !important; font-family:'Outfit',sans-serif;">🔑 Chave de API Requerida</h3>
        <p style="margin:10px 0 0 0; color:#8892B0; font-size:1rem; line-height:1.5;">
            Para habilitar as consultas inteligentes e a geração de minutas do <b>Legal AI Agent</b>, configure <code>GROQ_API_KEY</code>, <code>OLLAMA_API_KEY</code> ou <code>HF_TOKEN</code> em <code>.env</code> ou nos segredos do Streamlit.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if st.session_state.current_page == "chat":
    render_chat_page(t)
elif st.session_state.current_page == "docs":
    render_docs_page(t)
elif st.session_state.current_page == "juris":
    render_juris_page(t)
