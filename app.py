# app.py
import streamlit as st
import re
from html import escape

st.set_page_config(page_title="Validador de Transações — Passo a passo", layout="centered")

# -------------------------
# PADRÕES (igual ao seu)
# -------------------------
PATTERNS = {
    'DATA': re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'),
    'ID': re.compile(r'^TRX\d+$'),
    'TIPO': re.compile(r'^(CRED|DEB)ITO$', re.IGNORECASE),
    'CONTA': re.compile(r'^CONTA:\d+$'),
    'VALOR': re.compile(r'^\d+(\.\d{2})?$'),
    'MOEDA': re.compile(r'^[A-Z]{3}$'),
}

# -------------------------
# Tokenizer (adaptado)
# -------------------------
def tokenize_linha(linha):
    partes = re.split(r'\s*\|\s*', linha.strip())
    if len(partes) != 7:
        return None, [(None, f"Erro sintático: número de campos = {len(partes)} (esperado 7).")]

    ordem = ['DATA', 'ID', 'TIPO', 'CONTA', 'CONTA', 'VALOR', 'MOEDA']
    tokens = []
    erros = []
    for nome, parte in zip(ordem, partes):
        padrao = PATTERNS[nome]
        if padrao.match(parte):
            if nome == 'TIPO':
                parte_norm = parte.upper()
                parte_norm = parte_norm.replace('DEBITO', 'DÉBITO').replace('CREDITO', 'CRÉDITO')
                tokens.append((nome, parte_norm))
            else:
                tokens.append((nome, parte))
        else:
            tokens.append((nome, parte))
            erros.append((nome, parte))
    return tokens, erros

# -------------------------
# Geração dos passos em HTML (cores via CSS inline)
# -------------------------
def gerar_derivacao_html(tokens, erros):
    def ph(text):
        return f'<span style="font-family:monospace">{escape(text)}</span>'

    valid_color = "teal"    # valor válido (substituições)
    error_color = "crimson" # valor inválido
    sep_color = "gray"      # separador

    simbolos = []
    for i, (nome, _) in enumerate(tokens):
        if nome == 'DATA':
            simbolos.append('<Data>')
        elif nome == 'ID':
            simbolos.append('<Identificador>')
        elif nome == 'TIPO':
            simbolos.append('<Tipo>')
        elif nome == 'CONTA':
            simbolos.append('<Conta>')
        elif nome == 'VALOR':
            simbolos.append('<Valor>')
        elif nome == 'MOEDA':
            simbolos.append('<Moeda>')
        if i < len(tokens)-1:
            simbolos.append('SEP')

    passos = []
    passos.append(f"<b>&lt;Registro&gt;</b>")
    passos.append(f"<b>&lt;Linha&gt;</b>")
    # passo inicial com símbolos
    passos.append(' '.join(ph(s) if s != 'SEP' else ph('|') for s in simbolos))

    # valores intercalados (valor, '|', valor, '|', ...)
    valores = []
    for i, (_, v) in enumerate(tokens):
        valores.append(v)
        if i < len(tokens)-1:
            valores.append('|')

    corrente = simbolos.copy()
    idx_val = 0
    # substitui progressivamente e grava cada passo
    for i in range(len(corrente)):
        s = corrente[i]
        if s.startswith('<') or s == 'SEP':
            substituto = valores[idx_val]
            idx_val += 1
            if substituto == '|':
                corrente[i] = f'<span style="font-family:monospace;color:{sep_color}">|</span>'
            else:
                nome_esperado = tokens[i//2][0]  # mapeia posição
                # se o par (nome, substituto) estiver em erros -> vermelho
                if (nome_esperado, substituto) in erros:
                    corrente[i] = f'<span style="font-family:monospace;color:{error_color}">"{escape(substituto)}"</span>'
                else:
                    corrente[i] = f'<span style="font-family:monospace;color:{valid_color}">"{escape(substituto)}"</span>'
            passos.append(' '.join(corrente))

    return passos

# -------------------------
# Validação principal
# -------------------------
def validar_com_passos(linha):
    tokens, erros = tokenize_linha(linha)
    if tokens is None:
        return [], erros
    passos = gerar_derivacao_html(tokens, erros)
    return passos, erros

# -------------------------
# UI Streamlit
# -------------------------
st.title("Validador de Transações Bancárias")
st.write("Cole uma linha no formato: `DATA | ID | TIPO | CONTA | CONTA | VALOR | MOEDA`")
st.write("Exemplos: `2025-09-01T14:23:05Z | TRX123 | DEBITO | CONTA:123 | CONTA:456 | 150.00 | BRL`")

import streamlit as st

# st.title("Gramática Livre de Contexto")

# st.latex(r"""
# G = (V, \Sigma, R, S)
# """)

# st.latex(r"""
# V = \{\langle Registro\rangle, \langle Linha\rangle, \langle Data\rangle,
#          \langle Identificador\rangle ,\langle Tipo\rangle,\newline
#      \langle Conta\rangle, \langle Valor\rangle, \langle Moeda\rangle\}
# """)

# st.latex(r"""

# """)

# st.latex(r"S = \langle Registro\rangle")

# st.markdown("### Regras de Produção (R)")
# st.latex(r"""
# \begin{aligned}
# \langle Registro\rangle &\to \langle Linha\rangle \\
# \langle Linha\rangle &\to \langle Data\rangle \;|\; \langle Identificador\rangle \;|\; \langle Tipo\rangle \;|\; \langle Conta\rangle \;|\; \langle Conta\rangle \;|\; \langle Valor\rangle \;|\; \langle Moeda\rangle \\
# \langle Data\rangle &\to \texttt{DATA} \\
# \langle Identificador\rangle &\to \texttt{ID} \\
# \langle Tipo\rangle &\to \texttt{TIPO} \\
# \langle Conta\rangle &\to \texttt{CONTA} \\
# \langle Valor\rangle &\to \texttt{VALOR} \\
# \langle Moeda\rangle &\to \texttt{MOEDA}
# \end{aligned}
# """)


# area de input
linha = st.text_input("Linha de transação:", value=st.session_state.get("ultima_linha", ""))

col_a, col_b, col_c = st.columns([1,1,1])
if col_a.button("Validar"):
    passos, erros = validar_com_passos(linha)
    st.session_state['passos'] = passos
    st.session_state['erros'] = erros
    st.session_state['step_idx'] = 0
    st.session_state['ultima_linha'] = linha

# inicializa índices se não existirem
if 'step_idx' not in st.session_state:
    st.session_state['step_idx'] = 0
if 'passos' not in st.session_state:
    st.session_state['passos'] = []
if 'erros' not in st.session_state:
    st.session_state['erros'] = []

# if não há validação ainda, mostra instrução
if not st.session_state['passos']:
    st.info("Clique em **Validar** para gerar a derivação passo a passo.")
    st.stop()

# navegação de passos
n = len(st.session_state['passos'])
st.markdown("---")
col1, col2, col3 = st.columns([1,2,1])

with col1:
    if st.button("<< Voltar", key="voltar"):
        st.session_state['step_idx'] = max(0, st.session_state['step_idx'] - 1)
with col3:
    if st.button("Avançar >>", key="avancar"):
        st.session_state['step_idx'] = min(n-1, st.session_state['step_idx'] + 1)
with col2:
    st.write(f"**Passo {st.session_state['step_idx']} de {n-1}**")  # descontando headers (<Registro>, <Linha>)

# mostra o passo atual (usando HTML)
current = st.session_state['passos'][st.session_state['step_idx']]
st.markdown(current, unsafe_allow_html=True)

# mostrar todos os passos (expander)
with st.expander("Mostrar todos os passos"):
    for i, p in enumerate(st.session_state['passos']):
        st.markdown(f"**Passo {i}:** {p}", unsafe_allow_html=True)

# erros / detalhes
if st.session_state['erros']:
    st.error("⚠️ Erro(s) detectado(s) na validação.")
    with st.expander("Detalhes do(s) erro(s)"):
        for nome, parte in st.session_state['erros']:
            if nome is None:
                st.write(parte)
            else:
                st.write(f"Esperado: **{nome}**  |  Recebido: ❌ `{parte}`")

# ações adicionais
st.markdown("---")
if st.button("Reiniciar"):
    st.session_state.pop('passos', None)
    st.session_state.pop('erros', None)
    st.session_state.pop('step_idx', None)
    st.session_state.pop('ultima_linha', None)
    #st.experimental_rerun()
