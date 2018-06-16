# -*- coding: utf-8 -*-
"""
Created on Sun Jun 17 10:22:12 2018

@author: 北海若
"""

import model_v2 as mv2
import game_utils as gu
import time
import numpy as np
import dx_keycode as dxk


oldkeystate = [False for i in range(8)]
keystate = [False for i in range(8)]  # WSADJKLs
keysetting = [dxk.DIK_W,
              dxk.DIK_S,
              dxk.DIK_A,
              dxk.DIK_D,
              dxk.DIK_J,
              dxk.DIK_K,
              dxk.DIK_L,
              dxk.DIK_SPACE]


def act(result, my=0):
    for i in range(8):
        oldkeystate[i] = keystate[i]
    first_d = result // 9
    for i in range(4, 8):
        keystate[i] = first_d == i - 3
    next_d = (result % 9) // 3
    for i in range(2, 4):
        keystate[i] = next_d == i - 1
    if first_d == 0:
        if gu.fetch_posx()[1 - my] - gu.fetch_posx()[my] > 0:
            oldkeystate[2] = False
            keystate[2] = True
            oldkeystate[3] = True
            keystate[3] = False
        else:
            oldkeystate[2] = True
            keystate[2] = False
            oldkeystate[3] = False
            keystate[3] = True
    last_d = result % 3
    for i in range(0, 2):
        keystate[i] = last_d == i + 1
    if first_d == 0:
        if ((gu.fetch_operation()[1 - my] & 2 > 0)
                and gu.fetch_posy()[1 - my] < 0.01):
            oldkeystate[1] = False
            keystate[1] = True
            oldkeystate[0] = True
            keystate[0] = False
    for i in range(8):
        if (not oldkeystate[i]) and keystate[i]:
            gu.PressKey(keysetting[i])
        if (not keystate[i]) and oldkeystate[i]:
            gu.ReleaseKey(keysetting[i])


def play(my=0):
    en = 1 - my
    m = mv2.get_model()
    gu.update_proc()
    m.load_weights("D:/FXTZ.dat")
    print("Wait For Battle Detection...")
    while (gu.fetch_status() not in [0x05, 0x0e]):
        time.sleep(0.5)
    print("Battle Detected!")
    gu.update_base()
    char_act = []
    pos = []
    en_key = []
    my_key = []
    keys = [[], []]
    while gu.fetch_hp()[0] > 0 and gu.fetch_hp()[1] > 0:
        char_data = gu.fetch_char()
        px = gu.fetch_posx()
        py = gu.fetch_posy()
        if abs(px[en] - px[my]) > 0.4:
            if px[en] < px[my]:
                act(39, my)
            else:
                act(42, my)
            keys[0].append(gu.fetch_operation()[0])
            keys[1].append(gu.fetch_operation()[1])
            time.sleep(0.1)
            continue
        keys[0].append(gu.fetch_operation()[my])
        keys[1].append(gu.fetch_operation()[en])
        while len(keys[0]) > 30:
            keys[0] = keys[0][1:]
        while len(keys[1]) > 30:
            keys[1] = keys[1][1:]
        if len(keys[1]) < 30:
            continue
        char_act.append(np.array([char_data[my],
                        gu.fetch_action()[my],
                        char_data[en],
                        gu.fetch_action()[en]]))
        pos.append(np.array([px[my], py[my],
                             px[en], py[en],
                             px[en] - px[my],
                             py[en] - py[my]]))
        my_key.append(mv2.encode_keylist(keys[0], merge=1))
        en_key.append(mv2.encode_keylist(keys[1], merge=1))
        Y = m.predict([np.array(char_act),
                       np.array(pos),
                       np.array(en_key),
                       np.array(my_key)], batch_size=1)[0]
        char_act = []
        pos = []
        en_key = []
        my_key = []
        category = np.argmax(Y)
        # category = np.random.choice([x for x in range(45)], p=Y)
        time.sleep(0.06)
        act(category, my)


if __name__ == "__main__":
    while 1:
        play()