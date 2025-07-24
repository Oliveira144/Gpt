import streamlit as st
import matplotlib.pyplot as plt

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
    st.session_state.balance = None
if "profit" not in st.session_state:
    st.session_state.profit = 0.0
if "period" not in st.session_state:
    st.session_state.period = "Manhã"
if "locked" not in st.session_state:
    st.session_state.locked = False
if "bank_chart" not in st.session_state:
    st.session_state.bank_chart = []
if "meta_diaria" not in st.session_state:
    st.session_state.meta_diaria = 0.0
if "meta_periodo" not in st.session_state:
    st.session_state.meta_periodo = 0.0
if "stop_loss" not in st.session_state:
    st.session_state.stop_loss = 0.0
if "valor_aposta" not in st.session_state:
    st.session_state.valor_aposta = 0.0
if "odd" not in st.session_state:
    st.session_state.odd = 1.96  # Odd padrão do Football Studio

# ===============================
# CONFIGURAR BANCA E META
# ===============================
st.title("⚽ Painel Football Studio PRO")

if st.session_state.balance is None:
    st.subheader("💵 Configure sua Banca e Meta")
    banca_inicial = st.number_input("Informe sua banca inicial (R$)", min_value=50.0, value=200.0, step=10.0)
    meta_diaria = st.number_input("Informe sua meta de lucro diário (R$)", min_value=10.0, value=90.0, step=5.0)
    if st.button("✅ Confirmar"):
        st.session_state.balance = banca_inicial
        st.session_state.bank_chart = [banca_inicial]
        st.session_state.meta_diaria = meta_diaria
        st.session_state.meta_periodo = meta_diaria / 3  # Dividido em 3 períodos
        st.session_state.stop_loss = banca_inicial * 0.1  # Stop = 10% da banca
        st.session_state.valor_aposta = round((st.session_state.meta_periodo / 10) / (st.session_state.odd - 1), 2)
        st.rerun()
    st.stop()

# ===============================
# FUNÇÕES
# ===============================
def draw_history_balls(history):
    if not history:
        st.info("Nenhum resultado registrado ainda.")
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.axis("off")

    reversed_history = history[::-1]  # mais recente à esquerda
    rows = [reversed_history[i:i+9] for i in range(0, len(reversed_history), 9)]
    rows = rows[:10]  # máximo 10 linhas

    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            color = "red" if val == "🔴" else "blue" if val == "🔵" else "gold"
            circle = plt.Circle((c, -r), 0.4, color=color)
            ax.add_patch(circle)

    ax.set_xlim(-1, 9)
    ax.set_ylim(-len(rows), 1)
    st.pyplot(fig)

def detect_pattern(history):
    if len(history) < 5:
        return "Poucos dados", "?", 50, "Zona neutra"

    last = history[-1]
    sample = history[-18:]  # últimos 18 resultados
    next_move, confidence, alert = "?", 50, "Zona neutra"

    if len(set(sample[-4:])) == 1:
        next_move, confidence, alert = ("🔵" if last == "🔴" else "🔴"), 80, "Sequência longa detectada!"
    elif sample[-5:] in (["🔴","🔵","🔴","🔵","🔴"], ["🔵","🔴","🔵","🔴","🔵"]):
        next_move, confidence, alert = last, 70, "Alternância forte"
    elif last == "🟨":
        next_move, confidence, alert = "Aguardar", 50, "Empate estratégico"
    elif sample[-2:] in (["🔵","🔵"], ["🔴","🔴"]):
        next_move, confidence, alert = last, 75, "Possível virada"
    
    return "Padrão analisado", next_move, confidence, alert

def suggest_entry(next_move, confidence):
    valor = st.session_state.valor_aposta
    lucro_estimado = round(valor * (st.session_state.odd - 1), 2)
    retorno_total = round(valor + lucro_estimado, 2)

    if confidence >= 75 and next_move in ["🔴","🔵"]:
        return f"✅ Entrar em {next_move} | Aposta: R${valor} | Lucro: R${lucro_estimado} | Retorno: R${retorno_total}"
    elif 60 <= confidence < 75:
        return f"⚠ Entrada arriscada: {next_move} | Valor: R${valor}"
    else:
        return "⏳ Aguardar próximo sinal"

def check_limits():
    if st.session_state.profit >= st.session_state.meta_periodo:
        st.session_state.locked = True
        return "✅ Meta do período atingida!"
    elif st.session_state.profit <= -st.session_state.stop_loss:
        st.session_state.locked = True
        return "❌ Stop Loss atingido!"
    return None

# ===============================
# INTERFACE PRINCIPAL
# ===============================
st.subheader("📊 Status da Operação")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Período", st.session_state.period)
with col2:
    st.metric("Banca", f"R${st.session_state.balance:.2f}")
with col3:
    st.metric("Lucro", f"R${st.session_state.profit:.2f}")

col4, col5 = st.columns(2)
with col4:
    st.metric("Meta Período", f"R${st.session_state.meta_periodo:.2f}")
with col5:
    st.metric("Stop Loss", f"R${st.session_state.stop_loss:.2f}")

st.progress(min(st.session_state.profit / st.session_state.meta_periodo, 1.0))

msg = check_limits()
if msg:
    st.error(msg)

# Botões de registro de resultado
st.subheader("🎮 Registrar Resultado")
if not st.session_state.locked:
    colb1, colb2, colb3 = st.columns(3)
    with colb1:
        if st.button("🔴 Home"):
            st.session_state.history.append("🔴")
    with colb2:
        if st.button("🔵 Away"):
            st.session_state.history.append("🔵")
    with colb3:
        if st.button("🟨 Empate"):
            st.session_state.history.append("🟨")
else:
    st.warning("Entradas bloqueadas (meta/stop atingido)")

# Histórico visual
st.subheader("📜 Histórico (10x9)")
draw_history_balls(st.session_state.history)

# Análise inteligente
st.subheader("🔍 Análise e Sugestão")
padrao, next_move, confidence, alerta = detect_pattern(st.session_state.history)
st.write(f"**Padrão:** {padrao}")
st.write(f"**Próxima Tendência:** {next_move} ({confidence}%)")
st.write(f"**Alerta:** {alerta}")
if not st.session_state.locked:
    st.write(suggest_entry(next_move, confidence))

# Controle de ganho/perda
st.subheader("💰 Atualizar Banca")
col_g1, col_g2 = st.columns(2)
valor = st.session_state.valor_aposta
lucro_entrada = round(valor * (st.session_state.odd - 1), 2)

with col_g1:
    if st.button("✅ Ganhou"):
        st.session_state.profit += lucro_entrada
        st.session_state.balance += lucro_entrada
        st.session_state.bank_chart.append(st.session_state.balance)
with col_g2:
    if st.button("❌ Perdeu"):
        st.session_state.profit -= valor
        st.session_state.balance -= valor
        st.session_state.bank_chart.append(st.session_state.balance)

# Gráfico
st.subheader("📈 Evolução da Banca")
st.line_chart(st.session_state.bank_chart)

# Controles extras
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

if st.button("🗑 Limpar Histórico"):
    st.session_state.history = []
    st.success("Histórico limpo!")
