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
        self.rect.center = (50, HEIGHT // 2)
        self.speed = 1
        self.move_flag = False

        # 足音
        self.walk_se = pg.mixer.Sound("sound/asioto.mp3")

    def update(self, key_lst: list[bool], obstacles: pg.sprite.Group):
        """
        プレイヤー更新
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]

        actually_moved = False  # 実際に移動できたかを追跡する変数

        # めり込み防止チェック------------------------------
        # X方向の移動と衝突判定
        if sum_mv[0] != 0:
            self.rect.x += self.speed * sum_mv[0] # 先に仮移動させる
            if check_bound(self.rect)[0] is False or pg.sprite.spritecollideany(self, obstacles):   #もし画面外に出るか遮蔽物にぶつかるなら
                self.rect.x -= self.speed * sum_mv[0] # 引き戻された
            else:
                actually_moved = True # 引き戻されずに動ける

        # Y方向の移動と衝突判定
        if sum_mv[1] != 0:
            self.rect.y += self.speed * sum_mv[1] # 先に仮移動させる
            if check_bound(self.rect)[1] is False or pg.sprite.spritecollideany(self, obstacles):   #もし画面外に出るか遮蔽物にぶつかるなら
                self.rect.y -= self.speed * sum_mv[1] # 引き戻された
            else:
                actually_moved = True # 引き戻されずに動ける
        #-----------------------------------------------

        # 移動判定（キーが押されていて、かつ実際に動けた場合のみTrue）
        if sum_mv != [0, 0] and actually_moved:
            self.move_flag = True

            # 足音再生
            if not self.walk_se.get_num_channels():
                self.walk_se.play(-1)
        else:
            self.move_flag = False

            # 足音停止
            self.walk_se.stop()


class Obstacle(pg.sprite.Sprite):
    """
    遮蔽物に関するクラス
    """
    WIDTH = 30
    HEIGHT = 120
    BLOCK_IMAGE = None  # 初期化時は空にしておき、mainでロード

    def __init__(self, x: int, y: int):
        super().__init__()
        self.image = Obstacle.BLOCK_IMAGE
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

class Oni(pg.sprite.Sprite):
    """
    鬼に関するクラス
    """

    def __init__(self):
        super().__init__()
        self.image_back = pg.image.load("fig/2.png")
        self.image_front = pg.transform.flip(self.image_back, True, False)

        self.image = self.image_back
        self.rect = self.image.get_rect()

        # 開始時
        self.rect.center = (WIDTH - 50, HEIGHT // 2)
        self.look_flag = False

        # 次に振り向く時間
        self.next_turn = time.time() + random.uniform(5, 15)

        # 音声
        self.voice = pg.mixer.Sound("sound/sound.mp3")
        self.voice.play(-1)

        # 前回の配置座標を記憶するリスト
        self.prev_positions = []

    def generate_obstacles(self, obstacles_group: pg.sprite.Group):
        """
        ランダムな遮蔽物を生成する
        """
        obstacles_group.empty()  # 古いブロックをすべて消す
        new_positions = []

        # 個数は1〜3個
        num_obstacles = random.randint(1, 3)

        attempts = 0
        while len(new_positions) < num_obstacles and attempts < 100:    #もし100回試しても条件を満たす配置ができない時はあきらめる

            #出現エリアを 200 ～ 900 に制限
            x = random.randint(200, 900 - 30)
            #出現エリアを 50 ～ 480 に制限
            y = random.randint(50, HEIGHT - 120 - 50)

            # 密集・閉じ込め防止
            too_close = False
            for nx, ny in new_positions:
                if abs(nx - x) < 120 and abs(ny - y) < 180: #ブロック同士がxが120px以上,yは180px以上離れている
                    too_close = True
                    break

            # 1つ前の遮蔽物出現場所から120px以上離す
            for px, py in self.prev_positions:
                if abs(px - x) < 120 and abs(py - y) < 120:
                    too_close = True
                    break

            if not too_close:
                new_positions.append((x, y))
                obs = Obstacle(x, y)
                obstacles_group.add(obs)

        # 今回の配置を次回の1つ前の場所として記憶する
        self.prev_positions = new_positions

    def update(self, obstacles_group: pg.sprite.Group):
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
            if now >= self.next_turn:
                self.look_flag = False
                self.image = self.image_back

                # 後ろを向いたら遮蔽物をリフレッシュ
                self.generate_obstacles(obstacles_group)

                # 音声再生
                self.voice.play(-1)

                # 次の振り向き
                self.next_turn = now + random.uniform(5, 15)


def check_hidden(player: Player, obstacles: pg.sprite.Group) -> bool:
    """
    隠れ判定のルール（上下35px以上重なっていればセーフ）
    """
    REQUIRED_OVERLAP = 35  # プレイヤーの体のうち、縦に35ピクセル以上が遮蔽物の高さの中に収まっていればセーフ

    for obs in obstacles:
        # プレイヤーが遮蔽物より左側にいる
        if player.rect.right >= obs.rect.left:
            continue

        # 上下の重なり合っている部分の高さを求める
        overlap_top = max(player.rect.top, obs.rect.top)
        overlap_bottom = min(player.rect.bottom, obs.rect.bottom)

        # 重なりの高さを計算（プラスなら重なっている）
        overlap_height = overlap_bottom - overlap_top

        # 指定したピクセル数以上重なっていればセーフ
        if overlap_height >= REQUIRED_OVERLAP:
            return True  # 1つでも条件を満たすブロックがあればセーフ

    return False  # どのブロックの影にも隠れられていなければアウト


def draw_text(
    screen: pg.Surface,
    text: str,
    size: int,
    color: tuple[int, int, int],
    center: tuple[int, int],
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
    txt = fonto.render("Game Over", True, (255, 0, 0))
    screen.blit(txt, [WIDTH // 2 - 150, HEIGHT // 2])


def clear(screen: pg.Surface):
    fonto = pg.font.Font(None, 80)
    txt = fonto.render("Clear!", True, (0, 255, 0))
    screen.blit(txt, [WIDTH // 2 - 150, HEIGHT // 2])


def main():
    pg.display.set_caption("こうかとんが転んだ")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()
    bg_img = pg.Surface((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")

    loaded_img = pg.image.load("fig/block.png")
    Obstacle.BLOCK_IMAGE = pg.transform.scale(
        loaded_img, (Obstacle.WIDTH, Obstacle.HEIGHT)
    )

    player = Player()
    oni = Oni()

    obstacles = pg.sprite.Group()       # 遮蔽物を管理するグループ
    oni.generate_obstacles(obstacles)   # 初回スタート時の遮蔽物生成

    while True:
        key_lst = pg.key.get_pressed()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            # リスタート
            if event.type == pg.KEYDOWN and event.key == pg.K_r:
                return "restart"

        screen.blit(bg_img, [0, 0])
        player.update(key_lst, obstacles)
        oni.update(obstacles)

        # 描画
        obstacles.draw(screen)
        screen.blit(player.image, player.rect)
        screen.blit(oni.image, oni.rect)

        # ゲームオーバー判定
        if oni.look_flag and player.move_flag:
            # 遮蔽物の後ろに完全に隠れていればセーフ、そうでなければアウト
            if not check_hidden(player, obstacles):
                gameover(screen)
                pg.display.update()
                time.sleep(3)
                return

        # クリア判定
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