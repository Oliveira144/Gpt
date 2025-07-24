import streamlit as st

try:
    import matplotlib.pyplot as plt
    has_matplotlib = True
except ImportError:
    has_matplotlib = False

# ===============================
# CONFIGURAÇÃO INICIAL
# ===============================
st.set_page_config(page_title="Painel Football Studio PRO", layout="centered")

# ===============================
# ESTADO DA SESSÃO
# ===============================
if "history" not in st.session_state:
    st.session_state.history = []
if "balance" not in st.session_state:
    st.session_state.balance = 100.0
if "profit" not in st.session_state:
    st.session_state.profit = 0.0
if "period" not in st.session_state:
    st.session_state.period = "Manhã"
if "locked" not in st.session_state:
    st.session_state.locked = False
if "bank_chart" not in st.session_state:
    st.session_state.bank_chart = [100.0]

# ===============================
# CONFIGURAÇÕES DE META
# ===============================
DAILY_GOAL = 50.0
PERIODS = ["Manhã", "Tarde", "Noite"]
PERIOD_GOAL = DAILY_GOAL / 3
STOP_LOSS = 10.0

# ===============================
# FUNÇÕES
# ===============================
def draw_history_balls(history):
    if not history:
        st.info("Nenhum resultado registrado ainda.")
        return
    if not has_matplotlib:
        st.warning("Para visualizar o histórico com bolinhas, instale 'matplotlib'")
        st.write("Histórico simples:")
        st.write(" ".join(history))
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axis("off")

    # Quebrar histórico em linhas de 9 elementos (da esquerda para direita)
    rows = [history[i:i+9] for i in range(0, len(history), 9)]
    rows = rows[-10:]  # manter no máximo 10 linhas

    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            color = "red" if val == "🔴" else "blue" if val == "🔵" else "gold"
            circle = plt.Circle((c, -r), 0.4, color=color)
            ax.add_patch(circle)

    ax.set_xlim(-1, 9)
    ax.set_ylim(-len(rows), 1)
    st.pyplot(fig)

def detect_pattern(history):
    if len(history) < 3:
        return "Padrão insuficiente", "-", 0, 1, "Zona neutra"
    last = history[-1]
    pattern, next_move, confidence, level, alert = "Indefinido", "?", 50, 1, "Zona neutra"
    if len(history) >= 4 and len(set(history[-4:])) == 1:
        pattern, next_move, confidence, level, alert = "Sequência Longa", ("🔵" if last == "🔴" else "🔴"), 80, 2, "Quebra próxima!"
    elif len(history) >= 5 and history[-5:] in (["🔴","🔵","🔴","🔵","🔴"], ["🔵","🔴","🔵","🔴","🔵"]):
        pattern, next_move, confidence, level, alert = "Alternância", last, 70, 3, "Quebra de alternância!"
    elif last == "🟨":
        pattern, next_move, confidence, level, alert = "Empate Estratégico", "Aguardar", 50, 4, "Reset provável!"
    elif len(history) >= 6 and history[-2:] in (["🔵","🔵"], ["🔴","🔴"]):
        pattern, next_move, confidence, level, alert = "Virada", last, 75, 6, "Virada confirmada!"
    return pattern, next_move, confidence, level, alert

def suggest_entry(next_move, confidence):
    if confidence >= 75 and next_move in ["🔴","🔵"]:
        return f"✅ Entrar em {next_move} (Confiança {confidence}%)"
    elif 60 <= confidence < 75:
        return f"⚠ Entrada arriscada: {next_move} ({confidence}%)"
    else:
        return "⏳ Aguardar próximo sinal"

def check_limits():
    if st.session_state.profit >= PERIOD_GOAL:
        st.session_state.locked = True
        return "✅ Meta do período atingida!"
    elif st.session_state.profit <= -STOP_LOSS:
        st.session_state.locked = True
        return "❌ Stop Loss atingido!"
    return None

# ===============================
# INTERFACE PRINCIPAL
# ===============================
st.title("⚽ Painel Football Studio PRO")
st.write(f"**Período Atual:** {st.session_state.period}")
st.write(f"**Banca:** R${st.session_state.balance:.2f} | Lucro do período: R${st.session_state.profit:.2f}")
st.progress(min(st.session_state.profit / PERIOD_GOAL, 1.0))

limit_msg = check_limits()
if limit_msg:
    st.error(limit_msg)

# Botões de resultados
if not st.session_state.locked:
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔴 Home"):
            st.session_state.history.append("🔴")
    with col2:
        if st.button("🔵 Away"):
            st.session_state.history.append("🔵")
    with col3:
        if st.button("🟨 Empate"):
            st.session_state.history.append("🟨")
else:
    st.warning("Sugestões bloqueadas neste período.")

# Histórico visual (agora horizontal da esquerda para direita)
st.subheader("📜 Histórico Visual (Esquerda → Direita)")
draw_history_balls(st.session_state.history)

# Análise
pattern, next_move, confidence, level, alert = detect_pattern(st.session_state.history)
st.subheader("🔍 Análise Inteligente")
st.write(f"**Padrão Detectado:** {pattern}")
st.write(f"**Próxima Tendência:** {next_move} ({confidence}%)")
st.write(f"**Alerta:** {alert}")
st.write(f"**Nível de Manipulação:** {level}/9")

# Sugestão
st.subheader("🎯 Sugestão")
if not st.session_state.locked:
    st.write(suggest_entry(next_move, confidence))
else:
    st.write("⛔ Bloqueado - Meta/Stop atingido")

# Controle de ganhos/perdas
st.subheader("💰 Controle de Lucro")
col_g1, col_g2 = st.columns(2)
with col_g1:
    if st.button("+ Ganhou R$2"):
        st.session_state.profit += 2
        st.session_state.balance += 2
        st.session_state.bank_chart.append(st.session_state.balance)
with col_g2:
    if st.button("- Perdeu R$2"):
        st.session_state.profit -= 2
        st.session_state.balance -= 2
        st.session_state.bank_chart.append(st.session_state.balance)

# Evolução da banca
if has_matplotlib:
    st.subheader("📈 Evolução da Banca")
    st.line_chart(st.session_state.bank_chart)
else:
    st.info("Para ver gráfico da banca, instale 'matplotlib'.")

# Botão próximo período
if st.button("🔄 Próximo Período"):
    if st.session_state.period == "Manhã":
        st.session_state.period = "Tarde"
    elif st.session_state.period == "Tarde":
        st.session_state.period = "Noite"
    else:
        st.session_state.period = "Encerrado"
    st.session_state.profit = 0
    st.session_state.locked = False
    st.success("Novo período iniciado!")

# Reset geral
if st.button("🗑 Limpar Histórico"):
    st.session_state.history = []
    st.session_state.bank_chart = [st.session_state.balance]
    st.success("Histórico limpo!")
