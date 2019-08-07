# -*- coding: utf-8 -*-
"""
Created on Sun Aug  4 17:53:05 2019

@author: maton456
"""

#conda install -c conda-forge pyautogui 
#conda install pyaudio

import pyautogui as pgui
import math
import time
import numpy
import pyaudio
import threading
import matplotlib.pyplot as plt
from scipy import arange, cumsum, sin, linspace
from scipy import pi as mpi

        
def make_time_varying_sine(start_freq, end_freq, A, fs, sec = 5, phaze_start = 0):
    #周波数が変化するsin波
    freqs = linspace(start_freq, end_freq, num = int(round(fs * sec)))
    ### 角周波数の変化量
    phazes_diff = 2. * mpi * freqs / fs
    ### 位相
    phazes = cumsum(phazes_diff) + phaze_start
    ### サイン波合成
    ret = A * sin(phazes)
    phaze_last = phazes[-1]
    return ret, phaze_last


def play_tone(stream, length=1, rate=44100):
    #オーディオを鳴らす
    global sound_freq
    count = 0
    sound_freq_old = sound_freq
    phaze_start = 0
    while thread_2_flag:
        chunks = []
        ret, phaze_last = make_time_varying_sine(sound_freq_old, sound_freq, A, fs, sampling/1000, phaze_start)
        chunks.append(ret)
        chunk = numpy.concatenate(chunks)
        #print("sound_freq:" + str(sound_freq) + "sound_freq_old:" + str(sound_freq_old))
        sound_freq_old = sound_freq
        phaze_start = phaze_last
        stream.write(chunk.astype(numpy.float32).tostring())
        count = count + 1
        
    print("count:"+str(count))

def read_mouse(sensitivity=10, bias=196):
    global sound_freq
    global move_len_track
    w_0, h_0 = pgui.position()
    w_th, h_th = pgui.size()
    
    while thread_1_flag:
        #start = time.time()
        w_1, h_1 = pgui.position()
        move_len = math.sqrt((w_1 - w_0)**2 + (h_1 - h_0)**2)
        move_len_track.append(move_len)
        #print('move_len: ' + str(round(move_len)))
        if move_len == 0:
            continue
        #print('MOVE')
        sound_freq = round(move_len*sensitivity + bias)
        w_0, h_0 = w_1, h_1
        #time.sleep(0.001)
        #elapsed_time = time.time() - start
        #print ("elapsed_time:" + str(round(elapsed_time, 5)) + "[sec]")

if __name__ == '__main__':

    sampling = 10 #音の更新頻度(ms)
    sensitivity = 50 #マウスの感度
    bias = 0 #ベースの音程。196Hzはバイオリンの最低音、ソ
    A = 2 #音のボリューム。sin波の振幅
    play_time = 100 #修了までの時間(秒)
    fs = 44100
    sound_freq = 0
    move_len_track = []

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1, rate=fs, output=1)

    #スレッド設定
    thread_1 = threading.Thread(target=read_mouse, args=(sensitivity, bias))
    thread_2 = threading.Thread(target=play_tone, args=(stream, sampling/1000))
    thread_1_flag = True
    thread_2_flag = True
    
    #スレッド開始
    thread_1.start()
    thread_2.start()
    time.sleep(play_time)
    #スレッド修了
    thread_1_flag = False
    thread_2_flag = False

