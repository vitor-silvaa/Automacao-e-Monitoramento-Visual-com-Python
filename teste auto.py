import time
import datetime
import pyautogui
import csv
import cv2
import numpy as np
import random
from playwright.sync_api import sync_playwright
from threading import Thread

# =========================
# CONFIGURAÇÕES
# =========================
URL = "https://abcbet94.com/?id=676259993"
EMAIL = ""
SENHA = ""

COORD_INICIAL_X = 1099
COORD_INICIAL_Y = 925

COORD_JOGO_X = 959
COORD_JOGO_Y = 956

COORD_FIXO_52_X = 962
COORD_FIXO_52_Y = 686

CLIQUES_POR_HORA = 14
MINUTOS_OBRIGATORIOS = {53, 57, 59}

CSV_ARQUIVO = "observacoes_jogo.csv"

# =========================
# FUNÇÕES DE CLIQUE
# =========================
def clicar_por_coordenada(x, y, tipo="clique_jogo"):
    pyautogui.moveTo(x, y, duration=0.4)
    pyautogui.click()
    registrar_observacao(tipo)
    print(f"🖱️ Clique em ({x},{y})")

# =========================
# OBSERVADOR VISUAL
# =========================
ultima_imagem = None

def registrar_observacao(tipo_evento):
    global ultima_imagem

    screenshot = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

    brilho_medio = frame.mean()
    variacao = 0

    if ultima_imagem is not None:
        variacao = np.mean(cv2.absdiff(frame, ultima_imagem))

    ultima_imagem = frame

    with open(CSV_ARQUIVO, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.datetime.now().isoformat(),
            tipo_evento,
            round(brilho_medio, 2),
            round(variacao, 2)
        ])

def observador_loop():
    print("👁️ Observador visual iniciado")
    while True:
        registrar_observacao("observacao")
        time.sleep(10)

# =========================
# SEGUNDO ALEATÓRIO
# =========================
def segundo_aleatorio():
    return random.randint(35, 45)

# =========================
# CSV → MINUTOS QUENTES (ÍMPARES)
# =========================
minutos_quentes_csv = set()

def analisar_csv_periodicamente(intervalo_segundos=300):
    global minutos_quentes_csv
    print("🧠 Analisador de padrões iniciado")

    while True:
        time.sleep(intervalo_segundos)
        dados = []

        try:
            with open(CSV_ARQUIVO, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) != 4:
                        continue
                    timestamp, _, _, variacao = row
                    dados.append({
                        "dt": datetime.datetime.fromisoformat(timestamp),
                        "variacao": float(variacao)
                    })
        except FileNotFoundError:
            continue

        if len(dados) < 40:
            continue

        por_minuto = {}
        for d in dados:
            m = d["dt"].minute
            if m % 2 == 1:
                por_minuto.setdefault(m, []).append(d["variacao"])

        ranking = sorted(
            ((m, sum(v)/len(v)) for m, v in por_minuto.items()),
            key=lambda x: x[1],
            reverse=True
        )

        minutos_quentes_csv = {m for m, _ in ranking[:6]}

        print("\n🔥 Minutos quentes (CSV | ímpares):")
        print("   ", sorted(minutos_quentes_csv))

# =========================
# GERA HORÁRIOS (SOMENTE ÍMPARES)
# =========================
def gerar_cliques_da_hora(hora):
    minutos_impares = list(range(1, 60, 2))
    cliques = set(MINUTOS_OBRIGATORIOS)

    for m in sorted(minutos_quentes_csv):
        if len(cliques) < CLIQUES_POR_HORA:
            cliques.add(m)

    passo = max(1, len(minutos_impares) // CLIQUES_POR_HORA)

    for m in minutos_impares[::passo]:
        if len(cliques) >= CLIQUES_POR_HORA:
            break
        cliques.add(m)

    cliques = sorted(cliques)[:CLIQUES_POR_HORA]

    print(f"\n📅 Hora {hora:02d} – cliques (ímpares):")
    for m in cliques:
        print(f" ⏰ {hora:02d}:{m:02d}:35–45")

    return cliques

# =========================
# AUTOMAÇÃO PRINCIPAL
# =========================
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        channel="chrome",
        args=["--start-maximized"]
    )

    context = browser.new_context(no_viewport=True)
    page = context.new_page()

    page.goto(URL, timeout=60000)
    time.sleep(2)

    page.click('#ui-tabs-1-1')
    time.sleep(2)

    page.fill('input[placeholder="Digite o Número do Celular/E-mail"]', EMAIL)
    time.sleep(2)

    page.fill('input[placeholder="Insira a senha"]', SENHA)
    time.sleep(2)

    page.click('#insideLoginSubmitClick')
    time.sleep(3)

    for _ in range(3):
        try:
            page.click('.ui-dialog-close-box__icon', timeout=3000)
        except:
            pass

    page.click('div._btn-all-inside_1buei_70')
    time.sleep(2)

    page.click('button:has-text("Favoritos")')
    time.sleep(2)

    page.click('h4.name-inner._name-inner_1bflb_53')

    print("🎮 Jogo carregando...")
    time.sleep(10)

    clicar_por_coordenada(COORD_INICIAL_X, COORD_INICIAL_Y, "clique_inicial")

    Thread(target=observador_loop, daemon=True).start()
    Thread(target=analisar_csv_periodicamente, daemon=True).start()

    hora_atual = datetime.datetime.now().hour
    minutos_clique = gerar_cliques_da_hora(hora_atual)
    executados = set()
    segundos_alvo = {}

    while True:
        agora = datetime.datetime.now()

        if agora.hour != hora_atual:
            hora_atual = agora.hour
            minutos_clique = gerar_cliques_da_hora(hora_atual)
            executados.clear()
            segundos_alvo.clear()

        if agora.minute in minutos_clique and agora.minute not in executados:
            if agora.minute not in segundos_alvo:
                segundos_alvo[agora.minute] = segundo_aleatorio()

            if agora.second == segundos_alvo[agora.minute]:
                clicar_por_coordenada(COORD_JOGO_X, COORD_JOGO_Y)
                executados.add(agora.minute)

        if agora.minute == 52 and 35 <= agora.second <= 45:
            clicar_por_coordenada(
                COORD_FIXO_52_X,
                COORD_FIXO_52_Y,
                "clique_fixo_52"
            )

        time.sleep(1)
