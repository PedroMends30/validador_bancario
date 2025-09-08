# app.py
import streamlit as st
import re
from html import escape

st.set_page_config(page_title="Validador de Transações", layout="centered")

VALID_COLOR = "teal"
ERROR_COLOR = "crimson"
SEP_COLOR = "gray"


PATTERNS = {
    'DATA_HORA': re.compile(
        r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])"
        r"T([01]\d|2[0-3]):([0-5]\d):([0-5]\d)Z$"
    ),
    'TRANSACAO': re.compile(r'^trx\d{3}$'),
    'OPERACAO': re.compile(r'^(debito|credito)$', re.IGNORECASE),
    'CONTA': re.compile(r'^conta:\d{3}$', re.IGNORECASE),
    'VALOR': re.compile(r'^\d+\.\d{2}$'),
    'MOEDA': re.compile(r'^(usd|brl|eur)$', re.IGNORECASE),
}

ORDEM = [
    "DATA_HORA",
    "TRANSACAO",
    "OPERACAO",
    "CONTA_ORIGEM",
    "CONTA_DESTINO",
    "VALOR",
    "MOEDA"
]


def tokenize_linha(linha):
    partes = [p.strip() for p in linha.strip().split("|")]
    if len(partes) != 7:
        return None, [(None, f"Erro sintático: {len(partes)} campos (esperado 7).")]

    tokens = []
    erros = []
    for nome, parte in zip(ORDEM, partes):
        base = nome if not nome.startswith("CONTA") else "CONTA"
        padrao = PATTERNS[base]
        if padrao.match(parte):
            tokens.append((nome, parte))
        else:
            tokens.append((nome, parte))
            erros.append((nome, parte))
    return tokens, erros


def q_val(val, nome, erros):
    color = ERROR_COLOR if (nome, val) in erros else VALID_COLOR
    return f'<span style="font-family:monospace;color:{color}">"{escape(val)}"</span>'

def q_char(ch, nome, valor, erros):
    color = ERROR_COLOR if (nome, valor) in erros else VALID_COLOR
    return f'<span style="font-family:monospace;color:{color}">"{escape(ch)}"</span>'


def expandir_campo_html(nome, valor, erros):
    lines = []
    if nome == "DATA_HORA":
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z", valor or "")
        lines.append("&lt;DATA_HORA&gt; → &lt;ANO&gt;-&lt;MES&gt;-&lt;DIA&gt;T&lt;HORA&gt;:&lt;MIN&gt;:&lt;SEG&gt;Z")
        if not m:
            lines.append(f'<span style="font-family:monospace;color:{ERROR_COLOR}">Entrada inválida: {escape(str(valor))}</span>')
            return lines
        ano, mes, dia, hora, minu, seg = m.groups()
        lines.append("&lt;ANO&gt; → D D D D")
        lines.append(" ".join(q_char(d, nome, valor, erros) for d in ano))
        lines.append("&lt;MES&gt; → 0N | 10 | 11 | 12")
        lines.append(" ".join(q_char(d, nome, valor, erros) for d in mes))
        lines.append("&lt;DIA&gt; → 0N | 1D | 2D | 30 | 31")
        lines.append(" ".join(q_char(d, nome, valor, erros) for d in dia))
        lines.append("&lt;HORA&gt; → 0D | 1D | 20 | 21 | 22 | 23")
        lines.append(" ".join(q_char(d, nome, valor, erros) for d in hora))
        lines.append("&lt;MIN&gt; → 0D | 1D | 2D | 3D | 4D | 5D")
        lines.append(" ".join(q_char(d, nome, valor, erros) for d in minu))
        lines.append("&lt;SEG&gt; → D D")
        lines.append(" ".join(q_char(d, nome, valor, erros) for d in seg))
        # mostrar linha completa por caracteres (inclui '-' 'T' ':' 'Z')
        lines.append("<i>Caracteres:</i> " + " ".join(q_char(ch, nome, valor, erros) for ch in valor))
    elif nome == "TRANSACAO":
        lines.append("&lt;TRANSACAO&gt; → TRX D D D")
        lines.append(" ".join(q_char(ch, nome, valor, erros) for ch in valor))
    elif nome == "OPERACAO":
        lines.append("&lt;OPERACAO&gt; → debito | credito")
        lines.append(" ".join(q_char(ch, nome, valor, erros) for ch in valor))
    elif "CONTA" in nome:
        lines.append("&lt;CONTA&gt; → conta : D D D")
        lines.append(" ".join(q_char(ch, nome, valor, erros) for ch in valor))
    elif nome == "VALOR":
        lines.append("&lt;VALOR&gt; → &lt;DIGITOS&gt; . D D")
        if "." not in (valor or ""):
            lines.append(f'<span style="font-family:monospace;color:{ERROR_COLOR}">Entrada inválida: {escape(str(valor))}</span>')
            return lines
        intp, decp = (valor or "").split(".", 1)
        lines.append("&lt;DIGITOS&gt; → D | D &lt;DIGITOS&gt;")
        # mostra parte inteira e decimal como caracteres (o ponto também como terminal)
        chars = [*(intp), ".", *(decp)]
        lines.append(" ".join(q_char(ch, nome, valor, erros) for ch in chars))
    elif nome == "MOEDA":
        lines.append("&lt;MOEDA&gt; → L L L")
        lines.append(" ".join(q_char(ch, nome, valor, erros) for ch in valor))
    else:
        # fallback: mostrar o valor por caracteres
        lines.append(f"&lt;{escape(nome)}&gt; → (expansão)")
        lines.append(" ".join(q_char(ch, nome, valor, erros) for ch in (valor or "")))
    return lines


def gerar_derivacao_html(tokens, erros):
    # símbolos iniciais (pipes são literais)
    symbols = [
        "<DATA_HORA>", "|", "<TRANSACAO>", "|", "<OPERACAO>", "|",
        "<CONTA_ORIGEM>", "|", "<CONTA_DESTINO>", "|", "<VALOR>", "|", "<MOEDA>"
    ]

    passos = []
    passos.append("&lt;S&gt;")
    # cabeçalho com não-terminais
    header = " | ".join(["&lt;DATA_HORA&gt;", "&lt;TRANSACAO&gt;", "&lt;OPERACAO&gt;",
                         "&lt;CONTA_ORIGEM&gt;", "&lt;CONTA_DESTINO&gt;", "&lt;VALOR&gt;", "&lt;MOEDA&gt;"])
    passos.append(header)

    # corrente: inicia com symbol placeholders; pipes substituídos por span visual,
    corrente = symbols.copy()
    for i, s in enumerate(corrente):
        if s == "|":
            corrente[i] = f'<span style="font-family:monospace;color:{SEP_COLOR}">|</span>'

    # substituição progressiva: só substitui os não-terminais (0,2,4,...), nunca o '|'
    nonterminal_positions = [i for i, s in enumerate(symbols) if s != "|"]
    for pos in nonterminal_positions:
        token_idx = pos // 2
        nome, val = tokens[token_idx]
        corrente[pos] = q_val(val, nome, erros)
        passos.append(" ".join(corrente))

    # agora, para cada token, adicionar a expansão totalmente detalhada abaixo (não afeta a linha progressiva)
    for nome, val in tokens:
        # um separador visual entre blocos
        passos.append('<div style="height:6px"></div>')
        passos.extend(expandir_campo_html(nome, val, erros))

    return passos


def validar_com_passos(linha):
    tokens, erros = tokenize_linha(linha)
    if tokens is None:
        return [], erros
    passos = gerar_derivacao_html(tokens, erros)
    return passos, erros


st.title("Validador de Transações — Derivação Total")
st.write("Formato: `DATA_HORA | TRANSACAO | OPERACAO | CONTA_ORIGEM | CONTA_DESTINO | VALOR | MOEDA`")
st.write("Ex.: `2025-09-07T14:35:02Z | trx123 | debito | conta:001 | conta:999 | 1500.00 | brl`")

linha = st.text_input("Linha de transação:", value=st.session_state.get("ultima_linha", ""))

if st.button("Validar", key="validar_btn"):
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

if not st.session_state['passos']:
    st.info("Clique em **Validar** para gerar a derivação passo a passo.")
    st.stop()

# mostrar confirmação de sucesso / erro
if not st.session_state['erros']:
    st.success("Validação bem-sucedida! Todos os campos estão corretos.")
else:
    st.error("Erro(s) detectado(s) na validação.")


n = len(st.session_state['passos'])
st.markdown("---")
col1, col2, col3 = st.columns([1,2,1])

with col1:
    if st.button("<< Voltar", key="back_btn"):
        st.session_state['step_idx'] = max(0, st.session_state['step_idx'] - 1)
with col3:
    if st.button("Avançar >>", key="forward_btn"):
        st.session_state['step_idx'] = min(n-1, st.session_state['step_idx'] + 1)
with col2:
    st.write(f"**Passo {st.session_state['step_idx']} de {n-1}**")

current = st.session_state['passos'][st.session_state['step_idx']]
st.markdown(current, unsafe_allow_html=True)


with st.expander("Mostrar todos os passos"):
    for i, p in enumerate(st.session_state['passos']):
        st.markdown(f"**Passo {i}:** {p}", unsafe_allow_html=True)

# erros / detalhes
if st.session_state['erros']:
    st.error("Erro(s) detectado(s) na validação.")
    with st.expander("Detalhes do(s) erro(s)"):
        for nome, parte in st.session_state['erros']:
            if nome is None:
                st.write(parte)
            else:
                st.write(f"Esperado: **{nome}**  |  Recebido:  `{parte}`")

# reiniciar
if st.button("Reiniciar", key="reset_btn"):
    for k in ('passos','erros','step_idx','ultima_linha'):
        st.session_state.pop(k, None)
    st.rerun()
