import streamlit as st
import matplotlib.pyplot as plt
from collections import Counter

# ===============================
# CONFIGURAÇÕES INICIAIS
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
    st.session_state.odd = 1.96  # Odd padrão
if "prev_sinal" not in st.session_state:
    st.session_state.prev_sinal = None  # Para IA adaptativa
if "ajuste_conf" not in st.session_state:
    st.session_state.ajuste_conf = 0  # Ajuste adaptativo
if "resultado_registrado" not in st.session_state:
    st.session_state.resultado_registrado = False  # Controle para bloquear botões após clicar

# ===============================
# CONFIGURAR BANCA E META
# ===============================
st.title("⚽ Painel Football Studio PRO")

if st.session_state.balance is None:
    st.subheader("💵 Configure sua Banca e Meta")
    banca_inicial = st.number_input("Informe sua banca inicial (R$)", min_value=50.0, value=200.0, step=10.0)
    meta_diaria = st.number_input("Informe sua meta de lucro diário (R$)", min_value=10.0, value=90.0, step=5.0)
    confirmar = st.button("✅ Confirmar")
    if confirmar:
        st.session_state.balance = banca_inicial
        st.session_state.bank_chart = [banca_inicial]
        st.session_state.meta_diaria = meta_diaria
        st.session_state.meta_periodo = meta_diaria / 3
        st.session_state.stop_loss = banca_inicial * 0.1
        st.session_state.valor_aposta = round((st.session_state.meta_periodo / 10) / (st.session_state.odd - 1), 2)
        st.session_state.resultado_registrado = False
        st.success("Configuração salva com sucesso!")
        st.experimental_rerun()
    st.stop()
else:
    st.subheader("💵 Configuração atual")
    st.write(f"- **Banca inicial:** R${st.session_state.balance:.2f}")
    st.write(f"- **Meta diária:** R${st.session_state.meta_diaria:.2f}")
    st.write(f"- **Meta período:** R${st.session_state.meta_periodo:.2f}")
    st.write(f"- **Stop Loss:** R${st.session_state.stop_loss:.2f}")
    st.write(f"- **Valor da aposta:** R${st.session_state.valor_aposta:.2f}")

# ===============================
# FUNÇÕES
# ===============================
def draw_history_balls(history):
    if not history:
        st.info("Nenhum resultado registrado ainda.")
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.axis("off")

    reversed_history = history[::-1]
    rows = [reversed_history[i:i+9] for i in range(0, len(reversed_history), 9)]
    rows = rows[:10]

    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            color = "red" if val == "🔴" else "blue" if val == "🔵" else "gold"
            circle = plt.Circle((c, -r), 0.4, color=color)
            ax.add_patch(circle)

    ax.set_xlim(-1, 9)
    ax.set_ylim(-len(rows), 1)
    st.pyplot(fig)

def calcular_probabilidade(history):
    sample = history[-18:] if len(history) >= 18 else history
    if not sample:
        return {"🔴": 33.3, "🔵": 33.3, "🟨": 33.3}

    total = len(sample)
    contagem = Counter(sample)
    probs = {
        "🔴": (contagem.get("🔴", 0) / total) * 100,
        "🔵": (contagem.get("🔵", 0) / total) * 100,
        "🟨": (contagem.get("🟨", 0) / total) * 100
    }
    return probs

def nivel_manipulacao(history):
    sample = history[-18:]
    if len(sample) < 6:
        return 1, "Poucos dados"
    if len(set(sample[-5:])) == 1:
        return 7, "Surf longo, possível quebra"
    if sample[-5:] == ["🔴","🔵","🔴","🔵","🔴"] or sample[-5:] == ["🔵","🔴","🔵","🔴","🔵"]:
        return 4, "Alternância contínua"
    if "🟨" in sample[-3:]:
        return 6, "Empate como âncora"
    return 3, "Zona neutra"

def gerar_previsao(history):
    probs = calcular_probabilidade(history)
    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)

    next_move, confidence = sorted_probs[0][0], round(sorted_probs[0][1], 2)
    # IA adaptativa: ajuste baseado no último sinal falho
    if st.session_state.prev_sinal and st.session_state.prev_sinal != next_move:
        confidence = max(confidence - 5, 40)

    opcoes = " | ".join([f"{k} ({round(v, 1)}%)" for k, v in sorted_probs])
    return next_move, confidence, opcoes

def sugestao(next_move, confidence):
    valor = st.session_state.valor_aposta
    lucro = round(valor * (st.session_state.odd - 1), 2)
    retorno = round(valor + lucro, 2)
    if confidence >= 60:
        return f"✅ Entrar em {next_move} | Aposta: R${valor} | Lucro: R${lucro} | Retorno: R${retorno}"
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

# Histórico
st.subheader("📜 Histórico (10x9)")
draw_history_balls(st.session_state.history)

# Botões registrar resultado
st.subheader("🎮 Registrar Resultado")

if not st.session_state.locked and not st.session_state.resultado_registrado:
    colb1, colb2, colb3 = st.columns(3)
    with colb1:
        if st.button("🔴 Home"):
            st.session_state.history.append("🔴")
            st.session_state.resultado_registrado = True
    with colb2:
        if st.button("🔵 Away"):
            st.session_state.history.append("🔵")
            st.session_state.resultado_registrado = True
    with colb3:
        if st.button("🟨 Empate"):
            st.session_state.history.append("🟨")
            st.session_state.resultado_registrado = True
elif st.session_state.locked:
    st.warning("Entradas bloqueadas (meta/stop atingido)")
else:
    st.info("Aguarde atualização da banca para registrar novo resultado")

# Análise avançada
st.subheader("🔍 Análise Avançada")
nivel, alerta = nivel_manipulacao(st.session_state.history)
st.write(f"**Nível de Manipulação:** {nivel}/9 ({alerta})")

next_move, confidence, opcoes = gerar_previsao(st.session_state.history)
st.write(f"**Próxima tendência:** {next_move} ({confidence}%)")
st.write(f"**Cenários:** {opcoes}")
if not st.session_state.locked:
    st.write(sugestao(next_move, confidence))

# Controle de ganho/perda
st.subheader("💰 Atualizar Banca")
col_g1, col_g2 = st.columns(2)
valor = st.session_state.valor_aposta
lucro_entrada = round(valor * (st.session_state.odd - 1), 2)

with col_g1:
    if st.button("✅ Ganhou"):
        st.session_state.profit += lucro_entrada
        st.session_state.balance += lucro_entrada
        st.session_state.prev_sinal = next_move
        st.session_state.bank_chart.append(st.session_state.balance)
        st.session_state.resultado_registrado = False
with col_g2:
    if st.button("❌ Perdeu"):
        st.session_state.profit -= valor
        st.session_state.balance -= valor
        st.session_state.prev_sinal = next_move
        st.session_state.bank_chart.append(st.session_state.balance)
        st.session_state.resultado_registrado = False

# Gráfico da banca
st.subheader("📈 Evolução da Banca")
st.line_chart(st.session_state.bank_chart)

# Controles
if st.button("🔄 Próximo Período"):
    if st.session_state.period == "Manhã":
        st.session_state.period = "Tarde"
    elif st.session_state.period == "Tarde":
        st.session_state.period = "Noite"
    else:
        st.session_state.period = "Encerrado"
    st.session_state.profit = 0
    st.session_state.locked = False
    st.session_state.prev_sinal = None
    st.session_state.resultado_registrado = False
    st.success("Novo período iniciado!")

if st.button("🗑 Limpar Histórico"):
    st.session_state.history = []
    st.session_state.balance = None
    st.session_state.profit = 0.0
    st.session_state.bank_chart = []
    st.session_state.locked = False
    st.session_state.prev_sinal = None
    st.session_state.resultado_registrado = False
    st.success("Histórico e configurações reiniciados! Reconfigure banca e meta.")
    st.experimental_rerun()
