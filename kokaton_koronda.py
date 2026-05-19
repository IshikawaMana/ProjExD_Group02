import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100
HEIGHT = 650
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内にあるか判定する
    """
    yoko, tate = True, True

    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Player(pg.sprite.Sprite):
    """
    プレイヤーに関するクラス
    """

    delta = {
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self):
        super().__init__()
        self.image = pg.image.load("fig/alien1.png")
        self.rect = self.image.get_rect()

        # スタート位置
        self.rect.center = (50, HEIGHT//2)
        self.speed = 1
        self.move_flag = False

        # 足音
        self.walk_se = pg.mixer.Sound("sound/asioto.mp3")

    def update(self, key_lst: list[bool]):
        """
        プレイヤー更新
        """
        
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]

        self.rect.move_ip(
            self.speed*sum_mv[0],
            self.speed*sum_mv[1]
        )

        # 画面外判定
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(
                -self.speed*sum_mv[0],
                -self.speed*sum_mv[1]
            )

        # 移動判定
        if sum_mv != [0, 0]:
            self.move_flag = True

            # 足音再生
            if not self.walk_se.get_num_channels():
                self.walk_se.play(-1)

        else:
            self.move_flag = False
            
            # 足音停止
            self.walk_se.stop()


class Oni(pg.sprite.Sprite):
    """
    鬼に関するクラス
    """

    def __init__(self):
        super().__init__()
        self.image_back = pg.image.load("fig/2.png")
        self.image_front = pg.transform.flip(
            self.image_back,
            True,
            False
        )

        self.image = self.image_back
        self.rect = self.image.get_rect()

        # 開始時
        self.rect.center = (WIDTH-50, HEIGHT//2)
        self.look_flag = False

        # 次に振り向く時間
        self.next_turn = time.time() + random.uniform(5, 15)

        # 音声
        self.voice = pg.mixer.Sound("sound/sound.mp3")
        self.voice.play(-1)

    def update(self):
        """
        鬼更新
        """
        now = time.time()

        # 後ろ向き中
        if not self.look_flag:

            # ランダム時間経過で振り向く
            if now >= self.next_turn:
                self.look_flag = True
                self.image = self.image_front

                # 音声停止
                self.voice.stop()

                # 3秒後に後ろ向きへ戻る
                self.next_turn = now + 3

        # 前向き中
        else:
            # 3秒経過したら後ろ向き
            if now >= self.next_turn:
                self.look_flag = False
                self.image = self.image_back

                # 音声再生
                self.voice.play(-1)

                # 次の振り向き
                self.next_turn = now + random.uniform(5, 15)


def draw_text(
        screen: pg.Surface,
        text: str,
        size: int,
        color: tuple[int, int, int],
        center: tuple[int, int]
):
    """
    文字表示
    """

    font = pg.font.Font(None, size)
    txt = font.render(text, True, color)
    rect = txt.get_rect()
    rect.center = center
    screen.blit(txt, rect)


def gameover(screen: pg.Surface):
    fonto = pg.font.Font(None, 80)
    txt = fonto.render("Game Over", True, (255,0,0))
    screen.blit(txt,[WIDTH//2-150,HEIGHT//2])
    

def clear(screen: pg.Surface):
    fonto = pg.font.Font(None, 80)
    txt = fonto.render("Clear!", True, (0,255,0))
    screen.blit(txt,[WIDTH//2-150,HEIGHT//2])


def main():
    pg.display.set_caption("こうかとんが転んだ")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()

    bg_img = pg.Surface((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    player = Player()
    oni = Oni()

    while True:
        key_lst = pg.key.get_pressed()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            # リスタート
            if event.type == pg.KEYDOWN and event.key == pg.K_r:
                return "restart"

        screen.blit(bg_img, [0, 0])
        player.update(key_lst)
        oni.update()
        screen.blit(player.image, player.rect)
        screen.blit(oni.image, oni.rect)

        # ゲームオーバー
        if oni.look_flag and player.move_flag:
            gameover(screen)
            pg.display.update()
            time.sleep(3)
            return

        # クリア
        if player.rect.colliderect(oni.rect):
            clear(screen)
            pg.display.update()
            time.sleep(3)
            return

        pg.display.update()
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    while True:
        ret = main()
        if ret != "restart":
            break
    pg.quit()
    sys.exit()