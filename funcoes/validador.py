import re
from pprint import pprint

# Códigos de cor ANSI
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

PATTERNS = {
    # 30/10/2004 15:30:00
    # validar se a data é valida ex. 32/13/2020 25:61:61 é invalida
    # exemplo: 2025-09-01T14:23:05Z
    'DATA': re.compile(r'^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[0-2])-([0-9]{4})T(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])Z$'),
    'ID': re.compile(r'^TRX\d+$'),
    'TIPO': re.compile(r'^(CRED|DEB)ITO$', re.IGNORECASE),
    'CONTA': re.compile(r'^CONTA:\d+$'),
    'VALOR': re.compile(r'^\d+(\.\d{2})?$'),
    'MOEDA': re.compile(r'^[A-Z]{3}$'),
}

def tokenize_linha(linha):
    partes = re.split(r'\s*\|\s*', linha.strip())
    if len(partes) != 7:
        return None, f"{RED}Erro sintático: número de campos = {len(partes)} (esperado 7).{RESET}"
    
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
            tokens.append((nome, parte))  # Ainda adiciona para manter ordem de substituição
            erros.append((nome, parte))
    return tokens, erros

def gerar_derivacao(tokens, erros=[]):
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

    passos = [f"{BOLD}<Registro>{RESET}", f"{BOLD}<Linha>{RESET}", ' '.join(simbolos)]
    valores = []
    for i, (_, v) in enumerate(tokens):
        valores.append(v)
        if i < len(tokens)-1:
            valores.append('|')

    corrente = simbolos.copy()
    idx_val = 0
    for i in range(len(corrente)):
        s = corrente[i]
        if s.startswith('<') or s == 'SEP':
            substituto = valores[idx_val]
            idx_val += 1
            if substituto == '|':
                corrente[i] = f"{YELLOW}|{RESET}"
            else:
                nome_esperado = tokens[i//2][0]  # mapeia posição na lista original
                if (nome_esperado, substituto) in erros:
                    corrente[i] = f"{RED}\"{substituto}\"{RESET}"
                else:
                    corrente[i] = f"{CYAN}\"{substituto}\"{RESET}"
            passos.append(' '.join(corrente))
    return passos

def validar_com_passos(linha):
    tokens, erros = tokenize_linha(linha)
    passos = []

    if isinstance(erros, str):
        # Erro sintático de número de campos
        return passos, [(None, erros)]
    
    passos = gerar_derivacao(tokens, erros)
    return passos, erros

# ===========================
# EXECUÇÃO / USO
# ===========================
def exibir_validacao(linha_entrada):
    print(f"{BOLD}Linha de entrada:{RESET}")
    print(linha_entrada)
    print("\n" + "="*50 + "\n")

    passos, erros = validar_com_passos(linha_entrada)

    if erros:
        print(f"{RED}Erro encontrado durante a validação!{RESET}\n")
        print(f"{BOLD}Passos realizados (valores inválidos em vermelho):{RESET}")
        for i, p in enumerate(passos):
            print(f"  Passo {i}: {p}")
            input()
        print("\n" + "-"*40)
        print(f"{RED}Detalhes do(s) erro(s):{RESET}")
        for nome, parte in erros:
            if nome is None:
                print(f"  {parte}")  # erro de quantidade de campos
            else:
                print(f"  Esperado: {BOLD}{nome}{RESET}  |  Recebido: {RED}{parte}{RESET}")
    else:
        print(f"{GREEN}Linha aceita pela gramática!{RESET}\n")
        print(f"{BOLD}Derivação passo a passo:{RESET}\n")
        for i, p in enumerate(passos):
            print(f"{BOLD}Passo {i}:{RESET} {p}")
            input()
        print(f"\n{GREEN}✔️ Fim da derivação com sucesso!{RESET}")

if __name__ == "__main__":
    linha_exemplo = "30-11-2025T14:23:05Z | TRX12345 | CREDITO | CONTA:987654321 | CONTA:123456789 | 1500.00 | USD"
    
    exibir_validacao(linha_exemplo)
