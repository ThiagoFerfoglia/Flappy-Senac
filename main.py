import pygame
import random
import os
import sys

def resource_base():
    # Suporta execução normal e empacotada com PyInstaller (sys._MEIPASS)
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = resource_base()

def asset_path(*parts):
    # assets/ é a pasta raiz de recursos (imagens, áudios, etc.)
    return os.path.join(BASE_DIR, "assets", *parts)

escala = 1.5
# Parâmetros do jogo (bases)
LARGURA_TELA = int(400 * escala)
ALTURA_TELA = int(600 * escala)
LARGURA_CANO = int(60 * escala)
ESPACO_ENTRE_CANOS_BASE = int(160 * escala)
VELOCIDADE_CANO_BASE = 3
INTERVALO_CANOS_BASE = 1800  # milissegundos

# Limites e incrementos para a progressão
GRAVIDADE_BASE = 0.5
GRAVIDADE_INC = 0.05            # aumenta a gravidade a cada etapa
FORCA_PULO_BASE = -8
FORCA_PULO_MIN = -12            # pulo não ficará mais forte (mais negativo) que isso
FORCA_PULO_INC = -0.5           # torna o pulo mais “forte” (mais negativo) por etapa até o limite
VELOCIDADE_CANO_INC = 0.5       # aumenta velocidade do cano por etapa
ESPACO_ENTRE_CANOS_MIN = int(100 * escala)   # não fecha mais que isso
ESPACO_ENTRE_CANOS_DEC = int(10 * escala)    # diminui por etapa até o limite
INTERVALO_CANOS_MIN = 900       # não gera mais rápido que isso
INTERVALO_CANOS_DEC = 100       # diminui o intervalo por etapa até o limite

# Valores dinâmicos (atuais) que serão ajustados pela progressão
espaco_entre_canos_atual = ESPACO_ENTRE_CANOS_BASE
velocidade_cano_atual = VELOCIDADE_CANO_BASE
intervalo_canos_atual = INTERVALO_CANOS_BASE
gravidade = GRAVIDADE_BASE
forca_pulo = FORCA_PULO_BASE

# Controle de progressão
ultimo_degrau_aplicado = 0  # guarda em qual múltiplo de 5 já aplicamos a progressão

def progredir_dificuldade():
    global espaco_entre_canos_atual, velocidade_cano_atual, intervalo_canos_atual
    global gravidade, forca_pulo

    # Aumenta a gravidade
    gravidade += GRAVIDADE_INC

    # Torna o pulo mais "forte" (mais negativo), limitado por FORCA_PULO_MIN
    forca_pulo = max(FORCA_PULO_MIN, forca_pulo + FORCA_PULO_INC)

    # Aumenta a velocidade dos canos
    velocidade_cano_atual += VELOCIDADE_CANO_INC

    # Diminui o espaço entre canos, respeitando o mínimo
    espaco_entre_canos_atual = max(ESPACO_ENTRE_CANOS_MIN, espaco_entre_canos_atual - ESPACO_ENTRE_CANOS_DEC)

    # Diminui o intervalo de novos canos, respeitando o mínimo
    novo_intervalo = max(INTERVALO_CANOS_MIN, intervalo_canos_atual - INTERVALO_CANOS_DEC)
    if novo_intervalo != intervalo_canos_atual:
        intervalo_canos_atual = novo_intervalo
        pygame.time.set_timer(pygame.USEREVENT, intervalo_canos_atual)

# Inicializa o Pygame
pygame.init()
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Flappy Bird Simples")
clock = pygame.time.Clock()

# Cores
VERDE = (0, 200, 0)

# Imagem de fundo
fundo = pygame.image.load(asset_path("images", "fundo.png"))
fundo = pygame.transform.scale(fundo, (LARGURA_TELA, ALTURA_TELA))

# Imagens do personagem
personagem_img = pygame.image.load(asset_path("images", "personagem.png"))
personagem_img = pygame.transform.scale(personagem_img, (80, 80))
personagem_colidiu_img = pygame.image.load(asset_path("images", "personagem_colidiu.png"))
personagem_colidiu_img = pygame.transform.scale(personagem_colidiu_img, (80, 80))

# Animações (menu e gameover iguais: mesmos arquivos, mesma escala e posição)
menu1_raw = pygame.image.load(asset_path("images", "menu1.png"))
menu2_raw = pygame.image.load(asset_path("images", "menu2.png"))
menu1_scaled = pygame.transform.scale(menu1_raw, (700, 500))
menu2_scaled = pygame.transform.scale(menu2_raw, (700, 500))

animacao_frames = [menu1_scaled, menu2_scaled]             # menu
animacao_gameover_frames = [menu1_scaled, menu2_scaled]    # game over

# Controle de animação intercalada
animacao_index = 0
tempo_animacao = 300  # milissegundos por quadro
ultimo_tempo_animacao = pygame.time.get_ticks()

# Sons
som_pulo = pygame.mixer.Sound(asset_path("audio", "pulo.wav"))
som_pontuacao = pygame.mixer.Sound(asset_path("audio", "pontuacao.wav"))
som_gameover = pygame.mixer.Sound(asset_path("audio", "gameover.wav"))

# Música de fundo
pygame.mixer.music.load(asset_path("audio", "loop.wav"))
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.5)

# Personagem
personagem_x = 100
personagem_y = 300
velocidade_y = 0
personagem_largura = 60
personagem_altura = 40

# Pontuação e efeitos visuais
pontuacao = 0
texto_pontos = []  # cada item: {"x","y","tempo","duracao","float_px"}
parabens = []      # cada item: {"texto","tempo","duracao"}

# Lista de canos
canos = []

# Timer para gerar novos canos
pygame.time.set_timer(pygame.USEREVENT, intervalo_canos_atual)

# Estado do jogo: "menu", "jogando", "gameover"
estado_jogo = "menu"

def gerar_par_de_canos():
    topo_espaco = random.randint(80, ALTURA_TELA - 80 - espaco_entre_canos_atual)
    cano_superior = {'x': LARGURA_TELA, 'y': 0, 'altura': topo_espaco, 'pontuado': False}
    cano_inferior = {'x': LARGURA_TELA, 'y': topo_espaco + espaco_entre_canos_atual, 'altura': ALTURA_TELA - (topo_espaco + espaco_entre_canos_atual), 'pontuado': False}
    return cano_superior, cano_inferior

def resetar_estado_partida():
    global personagem_y, velocidade_y, canos, pontuacao, texto_pontos, parabens
    global espaco_entre_canos_atual, velocidade_cano_atual, intervalo_canos_atual
    global gravidade, forca_pulo, ultimo_degrau_aplicado

    personagem_y = 300
    velocidade_y = 0
    canos = []
    pontuacao = 0
    texto_pontos = []
    parabens = []

    espaco_entre_canos_atual = ESPACO_ENTRE_CANOS_BASE
    velocidade_cano_atual = VELOCIDADE_CANO_BASE
    intervalo_canos_atual = INTERVALO_CANOS_BASE
    gravidade = GRAVIDADE_BASE
    forca_pulo = FORCA_PULO_BASE
    ultimo_degrau_aplicado = 0

    pygame.time.set_timer(pygame.USEREVENT, intervalo_canos_atual)

rodando = True
while rodando:
    # Atualiza animação intercalada
    tempo_atual = pygame.time.get_ticks()
    if tempo_atual - ultimo_tempo_animacao > tempo_animacao:
        animacao_index = (animacao_index + 1) % 2
        ultimo_tempo_animacao = tempo_atual

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_SPACE:
                if estado_jogo == "menu":
                    estado_jogo = "jogando"
                    resetar_estado_partida()
                    pygame.mixer.music.play(-1)
                elif estado_jogo == "jogando":
                    velocidade_y = forca_pulo
                    som_pulo.play()
                elif estado_jogo == "gameover":
                    estado_jogo = "jogando"
                    resetar_estado_partida()
                    pygame.mixer.music.play(-1)

        if evento.type == pygame.USEREVENT and estado_jogo == "jogando":
            cano_sup, cano_inf = gerar_par_de_canos()
            canos.append(cano_sup)
            canos.append(cano_inf)

    if estado_jogo == "jogando":
        # Física
        velocidade_y += gravidade
        personagem_y += velocidade_y

        # Limites
        if personagem_y < 0:
            personagem_y = 0
            velocidade_y = 0
        if personagem_y > ALTURA_TELA - personagem_altura:
            personagem_y = ALTURA_TELA - personagem_altura
            velocidade_y = 0

        # Move canos
        for cano in canos:
            cano['x'] -= velocidade_cano_atual

        # Remove canos fora da tela
        canos = [cano for cano in canos if cano['x'] + LARGURA_CANO > 0]

        # Pontuação
        for i in range(0, len(canos), 2):
            cano = canos[i]
            if not cano['pontuado'] and cano['x'] + LARGURA_CANO < personagem_x:
                pontuacao += 1
                cano['pontuado'] = True
                if i + 1 < len(canos):
                    canos[i + 1]['pontuado'] = True

                texto_pontos.append({
                    "x": cano['x'] + LARGURA_CANO // 2,
                    "y": cano['altura'] + (espaco_entre_canos_atual // 2),
                    "tempo": pygame.time.get_ticks(),
                    "duracao": 600,
                    "float_px": 30
                })

                if pontuacao in (10, 50, 100):
                    if pontuacao == 10:
                        parabens.append({"texto": "10", "tempo": pygame.time.get_ticks(), "duracao": 1000})
                    elif pontuacao == 50:
                        parabens.append({"texto": "50", "tempo": pygame.time.get_ticks(), "duracao": 1200})
                    elif pontuacao == 100:
                        parabens.append({"texto": "100", "tempo": pygame.time.get_ticks(), "duracao": 1500})
                else:
                    som_pontuacao.play()

                if pontuacao % 5 == 0:
                    degrau_atual = pontuacao // 5
                    if degrau_atual > ultimo_degrau_aplicado:
                        progredir_dificuldade()
                        ultimo_degrau_aplicado = degrau_atual

        # Colisão
        personagem_rect = pygame.Rect(int(personagem_x + 5), int(personagem_y + 16), int(personagem_largura + 5), int(personagem_altura + 5))
        for cano in canos:
            cano_rect = pygame.Rect(cano['x'], cano['y'], LARGURA_CANO, cano['altura'])
            if personagem_rect.colliderect(cano_rect):
                if estado_jogo != "gameover":
                    som_gameover.play()
                    pygame.mixer.music.stop()
                estado_jogo = "gameover"

    # Desenho
    if estado_jogo == "menu":
        # Igual ao game over: tela preta + frames escalados na mesma posição
        tela.fill((0, 0, 0))
        frame = animacao_frames[animacao_index]
        tela.blit(frame, (-100, 200))

        # Texto de instrução
        fonte_menu = pygame.font.SysFont(None, 36)
        txt = fonte_menu.render("Pressione ESPAÇO para jogar", True, (200, 200, 200))
        tela.blit(txt, (LARGURA_TELA // 2 - txt.get_width() // 2, ALTURA_TELA // 2 - 30))

    elif estado_jogo == "jogando":
        tela.blit(fundo, (0, 0))
        for cano in canos:
            pygame.draw.rect(tela, VERDE, (cano['x'], cano['y'], LARGURA_CANO, cano['altura']))
        tela.blit(personagem_img, (personagem_x, int(personagem_y)))

        fonte_pontuacao = pygame.font.SysFont(None, 36)
        texto_pnt = fonte_pontuacao.render(str(pontuacao), True, (255, 255, 0))
        tela.blit(texto_pnt, (LARGURA_TELA // 2 - texto_pnt.get_width() // 2, 40))

        agora = pygame.time.get_ticks()
        fonte_parabens = pygame.font.SysFont(None, 60)
        novos_parabens = []
        for efeito in parabens:
            elapsed = agora - efeito["tempo"]
            if elapsed <= efeito["duracao"]:
                frac = elapsed / efeito["duracao"]
                y_base = ALTURA_TELA // 2
                y = y_base - int(frac * 40)
                surf_txt = fonte_parabens.render(efeito["texto"], True, (255, 215, 0))
                rect = surf_txt.get_rect(center=(LARGURA_TELA // 2, y))
                tela.blit(surf_txt, rect)
                novos_parabens.append(efeito)
        parabens = novos_parabens

        agora = pygame.time.get_ticks()
        novos_textos = []
        for t_item in texto_pontos:
            elapsed = agora - t_item["tempo"]
            if elapsed <= t_item["duracao"]:
                t_item["x"] -= velocidade_cano_atual
                frac = elapsed / t_item["duracao"]
                y_offset = int(frac * t_item["float_px"])
                surf_txt = fonte_pontuacao.render("+1", True, (255, 255, 0))
                tela.blit(surf_txt, (t_item["x"], t_item["y"] - y_offset))
                novos_textos.append(t_item)
        texto_pontos = novos_textos

    elif estado_jogo == "gameover":
        tela.fill((0, 0, 0))
        frame = animacao_gameover_frames[animacao_index]
        tela.blit(frame, (-100, 200))

        fonte = pygame.font.SysFont(None, 48)
        fonte_pontuacao = pygame.font.SysFont(None, 36)

        texto_go = fonte.render("Game Over", True, (255, 0, 0))
        tela.blit(texto_go, (LARGURA_TELA // 2 - texto_go.get_width() // 2, ALTURA_TELA // 2 - 120))

        texto_final = fonte_pontuacao.render(f"Pontuação: {pontuacao}", True, (255, 255, 255))
        tela.blit(texto_final, (LARGURA_TELA // 2 - texto_final.get_width() // 2, ALTURA_TELA // 2 - 70))

        dica = fonte_pontuacao.render("Pressione ESPAÇO para reiniciar", True, (200, 200, 200))
        tela.blit(dica, (LARGURA_TELA // 2 - dica.get_width() // 2, ALTURA_TELA // 2 - 30))

        tela.blit(personagem_colidiu_img, (personagem_x, int(personagem_y)))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()