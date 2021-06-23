from os import path
import pickle
import pygame
import random
from pygame.locals import (KEYDOWN,
                           KEYUP,
                           K_LEFT,
                           K_RIGHT,
                           QUIT,
                           K_ESCAPE, K_UP, K_DOWN, K_RCTRL, K_LCTRL,
                           K_SPACE,K_TAB, K_m, K_s
                           )
from fundo import (Fundo,
                   Telas)
from elementos import ElementoSprite
import random

class Jogo:
    def __init__(self, fullscreen=False):
        self.elementos = {}
        # inicializa o pygame
        pygame.mixer.pre_init()
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()

        # Inicializações relativas ao som
        sons_dir = path.join(path.dirname(__file__), 'sons')
        self.som_disparo = pygame.mixer.Sound(path.join(sons_dir, 'som_laser.wav'))
        self.som_atingido = pygame.mixer.Sound(path.join(sons_dir, 'som_atingido.wav'))
        self.sons_explosao = []
        for som in ['som_explosao1.wav', 'som_explosao2.wav', 'som_explosao3.wav']:
            self.sons_explosao.append(pygame.mixer.Sound(path.join(sons_dir, som)))

        self.music_paused = False
        self.som_paused = False
        pygame.mixer.music.load(path.join(sons_dir, 'background_music.wav'))
        pygame.mixer.music.set_volume(0.75)

        # inicializações relativas à tela
        flags = pygame.DOUBLEBUF
        if fullscreen:
            flags |= pygame.FULLSCREEN

        infoObject = pygame.display.Info()
        user_screen = (infoObject.current_w, infoObject.current_h)
        dim = int(user_screen[1]*0.85)
        self.screen_size = (int(dim*1.2), dim)


        self.tela = pygame.display.set_mode(self.screen_size, flags=flags, depth=16)
        self.fundo = Fundo()
        self.iniciando = True
        self.img_tela_inicial = Telas('tela_inicial.png', self.screen_size)
        self.img_tela_final = Telas('tela_final.png',self.screen_size)
        self.img_tela_pausa = Telas('tela_pause.png',self.screen_size)
        self.img_tela_win = Telas('tela_win.png',self.screen_size)

        self.jogador = Jogador([0.45*self.screen_size[0], 0.8*self.screen_size[1]], 5)
        self.interval = 0
        self.nivel = 0
        self.fonte = pygame.font.SysFont('arial', 42)
        fonte_dir = path.join(path.dirname(__file__), 'fonte')
        try:
            self.fonte2 = pygame.font.Font(path.join(fonte_dir, 'fonte.ttf'), 42)
        except:
            self.fonte2 = pygame.font.Font(path.join(fonte_dir, 'fonte.TTF'), 42)

        self.vida_virus = 0

        pygame.mouse.set_visible(0)
        pygame.display.set_caption('Corona Shooter')
        self.run = True
        self.pause = False


        # Animações de Explosão
        self.explosoes_frames = []
        for i in range(32):
            filename = f'explosao_{i}.png'
            self.explosoes_frames.append(filename)


    def escreve_placar(self,x_score,y_score,x_vidas,y_vidas):
        heart = "♥"
        vidas = self.fonte.render(f'{self.jogador.get_lives()*heart}', 1, (255, 0, 0))
        score = self.fonte2.render(f'Score: {self.jogador.pontos}', 1, (255,255,255))
        vidas_rect = vidas.get_rect(midtop=(self.screen_size[0]*x_vidas, self.screen_size[1]*y_vidas))
        score_rect = score.get_rect(midtop=(self.screen_size[0]*x_score, self.screen_size[1]*y_score))

        self.tela.blit(vidas, vidas_rect)
        self.tela.blit(score, score_rect)

    def manutenção(self):
        r = random.randint(0, 100)
        x = random.randint(1, self.screen_size[0])
        virii = self.elementos["virii"]
        if r > (10 * len(virii)):
            lives = self.vida_virus
            if self.nivel == 2:
                enemy = Virus([0,0], lives, image='virus-chefao.png')
            if self.nivel == 1:
                enemy = Virus([0, 0], lives,image='virus2.png')
            if self.nivel == 0:
                enemy = Virus([0, 0], lives)

            size = enemy.get_size()
            enemy.set_pos([min(max(x, size[0] / 2), self.screen_size[0] - size[0] / 2), size[1] / 2])
            colisores = pygame.sprite.spritecollide(enemy, virii, False)
            if colisores:
                return
            self.elementos["virii"].add(enemy)


    def muda_nivel(self):
        xp = self.jogador.get_pontos()
        if xp == 5:
            self.nivel = 1
            self.jogador.set_lives(self.jogador.get_lives() + 3)
            self.jogador.set_pontos(self.jogador.get_pontos() + 1)
            for v in self.elementos['virii']:
                v.kill()
                v.set_lives(2)
                old_size = v.get_size()
                v.scale(old_size)
                self.constroi_nivel()
        if xp == 20:
            self.nivel = 2
            self.jogador.set_lives(self.jogador.get_lives() + 3)
            self.jogador.set_pontos(self.jogador.get_pontos() + 1)
            for v in self.elementos['virii']:
                v.kill()
                v.set_lives(20)
                old_size = v.get_size()
                v.scale(old_size)
                self.constroi_nivel()

    def constroi_nivel(self):
        if self.nivel == 1:
            self.fundo = Fundo("sky.png")
            self.vida_virus = 1
        if self.nivel == 2:
            self.fundo = Fundo("street.jpg")
            self.vida_virus = 20

    def atualiza_elementos(self, dt):
        self.fundo.update(dt)
        for v in self.elementos.values():
            v.update(dt)

    def desenha_elementos(self):
        self.fundo.draw(self.tela)
        for v in self.elementos.values():
            v.draw(self.tela)

    def verifica_impactos(self, elemento, list, action):
        """
        Verifica ocorrência de colisões.
        :param elemento: Instância de RenderPlain ou seja um grupo de sprites
        :param list: lista ou grupo de sprites
        :param action: função a ser chamada no evento de colisão
        :return: lista de sprites envolvidos na colisão
        """
        if isinstance(elemento, pygame.sprite.RenderPlain):
            hitted = pygame.sprite.groupcollide(elemento, list, 1, 0)
            for v in hitted.values():
                for o in v:
                    Explosao(o.get_pos(), self.explosoes_frames, self.elementos['explosoes'])
                    random.choice(self.sons_explosao).play()
                    action(o)
            return hitted

        elif isinstance(elemento, pygame.sprite.Sprite):
            if pygame.sprite.spritecollide(elemento, list, 1):
                self.som_atingido.play()
                Explosao(elemento.get_pos(), self.explosoes_frames, self.elementos['explosoes'])
                action()
            return elemento.morto

    def trata_eventos_constantes(self, event):
        if event.type == pygame.QUIT:
            self.run = False
            self.iniciando = False
            self.finalizando = False
            self.pause = False
        if event.type == KEYDOWN:
            key = event.key
            if key == K_ESCAPE:
                self.run = False
            elif key == K_m:
                pygame.mixer.music.unpause() if self.music_paused else pygame.mixer.music.pause()
                self.music_paused = not self.music_paused
            elif key == K_s:
                if self.som_paused:
                    for som in [self.som_disparo, self.som_atingido]:
                        pygame.mixer.Sound.set_volume(som, 100)
                    for som in self.sons_explosao:
                            pygame.mixer.Sound.set_volume(som, 100)
                    self.som_paused = not self.som_paused
                else:
                    for som in [self.som_disparo, self.som_atingido]:
                        pygame.mixer.Sound.set_volume(som, 0)
                    for som in self.sons_explosao:
                        pygame.mixer.Sound.set_volume(som, 0)
                    self.som_paused = not self.som_paused





    def trata_eventos_jogando(self):
        event = pygame.event.poll()
        self.trata_eventos_constantes(event)
        if event.type == KEYDOWN:
            key = event.key
            if key == K_SPACE:
                self.pause = True
            elif key in (K_LCTRL, K_RCTRL):
                self.interval = 0
                self.jogador.atira(self.elementos["tiros"], self.som_disparo)
            elif key == K_UP:
                self.jogador.accel_top()
            elif key == K_DOWN:
                self.jogador.accel_bottom()
            elif key == K_RIGHT:
                self.jogador.accel_right()
            elif key == K_LEFT:
                self.jogador.accel_left()

        if event.type == KEYUP:
            key = event.key
            if key == K_UP:
                self.jogador.accel_zero()
            elif key == K_DOWN:
                self.jogador.accel_zero()
            elif key == K_RIGHT:
                self.jogador.accel_zero()
            elif key == K_LEFT:
                self.jogador.accel_zero()

        keys = pygame.key.get_pressed()
        if self.interval > 10:
            self.interval = 0
            if keys[K_RCTRL] or keys[K_LCTRL]:
                self.jogador.atira(self.elementos["tiros"], self.som_disparo)

    def ação_elemento(self):
        """
        Executa as ações dos elementos do jogo.
        :return:
        """

        self.verifica_impactos(self.jogador, self.elementos["tiros_inimigo"],
                               self.jogador.alvejado)
        if self.jogador.morto:
            self.tela_final()
            return 0

        # Verifica se o personagem trombou em algum inimigo
        self.verifica_impactos(self.jogador, self.elementos["virii"],
                               self.jogador.colisão)
        if self.jogador.morto:
            self.tela_final()
            return 0
        # Verifica se o personagem atingiu algum alvo.
        hitted = self.verifica_impactos(self.elementos["tiros"],
                                        self.elementos["virii"],
                                        Virus.alvejado)

        # Aumenta a pontos baseado no número de acertos:
        self.jogador.set_pontos(self.jogador.get_pontos() + len(hitted))

    # Verifica se o usuário pausou o jogo e o mantém em uma tela de pausa
    def verifica_pausa(self):
        while(self.pause):
            self.img_tela_pausa.draw(self.tela)
            self.escreve_placar(x_score=0.53, y_score=0.65,
                                x_vidas=0.53, y_vidas=0.70)
            pygame.display.flip()
            event = pygame.event.poll()
            #evento para sair do jogo ao clicar no X da janela
            self.trata_eventos_constantes(event)
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    self.run = False
                    self.pause = False
                elif event.key == pygame.K_TAB:
                    self.salva_jogo()
                #evento para fechar a janela ao apertar esc
                elif event.key == K_SPACE:
                    self.run = True
                    self.pause = False

    def carrega_jogo(self):
        teste = pickle.load(open("save.p", "rb"))
        print(teste)
        self.nivel = teste['nivel']
        self.jogador.set_pontos(teste['pontos'])
        self.jogador.set_lives(teste['vidas'])
        self.jogador.set_pos(teste['pos_jogador'])
        self.constroi_nivel()
        print('Jogo carregado com sucesso! Nível do jogo anterior' + str(teste))

    def salva_jogo(self):
        pickle.dump({'nivel':self.nivel,
                     'pontos':self.jogador.get_pontos(),
                     'vidas':self.jogador.get_lives(),
                     'pos_jogador':self.jogador.get_pos()},open("save.p", "wb"))
        print('Jogo salvo com sucesso')  # substituir por mensagem de verdade

    def tela_inicial(self):
        self.img_tela_inicial.draw(self.tela)

        pygame.display.flip()
        while self.iniciando:
            event = pygame.event.poll()
            self.trata_eventos_constantes(event)
            if event.type in (KEYDOWN, KEYUP):
                key = event.key
                if key == K_ESCAPE:
                    self.run = False
                    self.iniciando = False
                if key == K_SPACE:
                    self.iniciando = False
                if key == K_SPACE:
                    self.musica_ligada = False
                # Caso o usuário aperte TAB, carrega o jogo salvo
                if key == K_TAB:
                    self.iniciando = False
                    self.carrega_jogo()

    def tela_final(self):
        self.finalizando = True
        self.img_tela_final.draw(self.tela)
        self.escreve_placar(x_score=0.51, y_score=0.51,
                            x_vidas=0.45, y_vidas=0.53)
        pygame.display.flip()
        while self.finalizando:
            event = pygame.event.poll()
            self.trata_eventos_constantes(event)
            if event.type in (KEYDOWN, KEYUP):
                key = event.key
                if key == K_SPACE:
                    self.finalizando = False
                    self.run = True
                    self.fundo=Fundo()
                    self.nivel =0
                    self.vida_virus = 0
                    self.jogador = Jogador([0.45 * self.screen_size[0], 0.7 * self.screen_size[0]], 5)
                    self.loop()
                elif key == K_ESCAPE:
                    self.run = False
                    final = False

    def loop(self):
        clock = pygame.time.Clock()
        pygame.mixer.music.play(loops=-1)
        self.tela_inicial()
        dt = 16
        self.elementos['virii'] = pygame.sprite.RenderPlain()
        self.elementos['jogador'] = pygame.sprite.RenderPlain(self.jogador)
        self.elementos['tiros'] = pygame.sprite.RenderPlain()
        self.elementos['explosoes'] = pygame.sprite.RenderPlain()
        self.elementos['tiros_inimigo'] = pygame.sprite.RenderPlain()

        while self.run:
            clock.tick(1000/dt)
            self.trata_eventos_jogando()
            self.verifica_pausa()
            self.ação_elemento()
            self.manutenção()
            # Atualiza Elementos
            self.atualiza_elementos(dt)
            # Desenhe no back buffer
            self.desenha_elementos()
            self.escreve_placar(x_score=0.75, y_score=0,
                                x_vidas=0.15, y_vidas=0)
            self.muda_nivel()
            #texto = self.fonte.render(f"Vidas: {self.jogador.get_lives()}", True, (255, 255, 255), (0, 0, 0))

            pygame.display.flip()


class Nave(ElementoSprite):
    def __init__(self, position, lives=0, speed=[0, 0], image=None, new_size=[83, 248]):
        self.acceleration = [3, 3]
        if not image:
            image = "seringa.png"
        super().__init__(image, position, speed, new_size)
        self.set_lives(lives)

    def get_lives(self):
        return self.lives

    def set_lives(self, lives):
        self.lives = lives

    def colisão(self):
        if self.get_lives() <= 0:
            self.kill()
        else:
            self.set_lives(self.get_lives() - 1)

    def atira(self, lista_de_tiros, image=None):
        s = list(self.get_speed())
        s[1] *= 2
        Tiro(self.get_pos(), s, image, lista_de_tiros)

    def alvejado(self):
        if self.get_lives() <= 0:
            self.kill()
        else:
            self.set_lives(self.get_lives() - 1)

    @property
    def morto(self):
        return self.get_lives() == 0

    def accel_top(self):
        speed = self.get_speed()
        self.set_speed((speed[0], speed[1] - self.acceleration[1]))

    def accel_bottom(self):
        speed = self.get_speed()
        self.set_speed((speed[0], speed[1] + self.acceleration[1]))

    def accel_left(self):
        speed = self.get_speed()
        self.set_speed((speed[0] - self.acceleration[0], speed[1]))

    def accel_right(self):
        speed = self.get_speed()
        self.set_speed((speed[0] + self.acceleration[0], speed[1]))
        
    def accel_zero(self):
        self.set_speed([0,0])


class Virus(Nave):
    def __init__(self, position, lives=0, image=None, size=(75, 75)):
        if not image:
            image = "virus.png"
        super().__init__(position, lives, [0, 0], image, size)

    def velocidade_virus(self):
        x = random.randrange(-2, 2)
        y = random.randrange(2, 5)
        move_speed = (x, y)
        return move_speed

    def set_speed(self, speed):
        move_speed = self.velocidade_virus()
        self.speed = move_speed


class Jogador(Nave):
    """
    A classe Player é uma classe derivada da classe GameObject.
       No entanto, o personagem não morre quando passa da borda, este só
    interrompe o seu movimento (vide update()).
       E possui experiência, que o fará mudar de nivel e melhorar seu tiro.
       A função get_pos() só foi redefinida para que os tiros não saissem da
    parte da frente da nave do personagem, por esta estar virada ao contrário
    das outras.
    """

    def __init__(self, position, lives=10, image=None, new_size=[62, 186]):
        if not image:
            image = "seringa.png"
        super().__init__(position, lives, [0, 0], image, new_size)
        self.pontos = 0

    def update(self, dt):
        move_speed = (self.speed[0] * dt / 16,
                      self.speed[1] * dt / 16)
        self.rect = self.rect.move(move_speed)

        if (self.rect.right > self.area.right):
            self.rect.right = self.area.right

        elif (self.rect.left < 0):
            self.rect.left = 0

        if (self.rect.bottom > self.area.bottom):
            self.rect.bottom = self.area.bottom

        elif (self.rect.top < 0):
            self.rect.top = 0

    def get_pos(self):
        return (self.rect.center[0], self.rect.top)

    def get_pontos(self):
        return self.pontos

    def set_pontos(self, pontos):
        self.pontos = pontos

    def atira(self, lista_de_tiros, som_disparo, image=None):
        som_disparo.play()
        l = 1
        if self.pontos > 500:
            l = 3

        p = self.get_pos()
        speeds = self.get_fire_speed(l)
        for s in speeds:
            Tiro(p, s, image, lista_de_tiros)

    def get_fire_speed(self, shots):
        speeds = []

        if shots <= 0:
            return speeds

        if shots == 1:
            speeds += [(0, -5)]

        if shots > 1 and shots <= 3:
            speeds += [(0, -5)]
            speeds += [(-2, -3)]
            speeds += [(2, -3)]

        return speeds


class Tiro(ElementoSprite):
    def __init__(self, position, speed=None, image=None, list=None):
        if not image:
            image = "tiro.png"
        super().__init__(image, position, speed)
        if list is not None:
            self.add(list)

class Explosao(ElementoSprite):
    def __init__(self, position, lista_imgs, lista_de_explosoes):
        self.frame = 0
        self.lista_imgs = lista_imgs
        image = lista_imgs[0]
        super().__init__(image, position, 0)
        self.add(lista_de_explosoes)

        self.ultimo_update = pygame.time.get_ticks()
        self.tempo_de_espera = 30

    def update(self, dt):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_update > self.tempo_de_espera:
            self.ultimo_update = agora
            self.frame += 1
            if self.frame < len(self.lista_imgs):
                image = self.lista_imgs[self.frame]
                self.set_image(image)
            else:
                self.kill()

if __name__ == '__main__':
    J = Jogo(fullscreen=False)
    J.loop()
