# -*- coding: utf-8 -*-
"""
Created on Sun Aug  4 17:53:05 2019
@author: maton456
"""

import pyautogui as pgui
import math
import time
import numpy as np
import pyaudio
import threading
import matplotlib.pyplot as plt
from collections import deque


class mouseDJ:
        
    def __init__(self, sampling=0.01, sensitivity=50, bias=0, volume=2, fs=44100):
        self.move_len_track = []
        self.chunk_plot = deque([], 1000)
        self.sound_freq = 0
        self.sampling = sampling  # スクラッチ音の更新頻度(秒)
        self.sensitivity = sensitivity  # マウスの移動感度
        self.bias = bias  # スクラッチ音の周波数のオフセット(Hz)。例えば196Hzはバイオリンの最低音、ソ
        self.volume = volume  # スクラッチ音のボリューム。sin波の振幅。2を超えると音が歪むかも
        self.fs = fs  # PyAudioの周波数
        

    def __del__(self):
        if (self.thread_1_flag == True) or (self.thread_2_flag == True):
            self.finish()
    

    def start(self, endless=True, play_time_sec=0):
        if (type(play_time_sec) != int) or (play_time_sec < 0):
            print('Error: Set positive int into play_time')
            return()
        
        # オーディオ設定
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paFloat32,
                                  channels=1, rate=self.fs, output=1)
        # スレッド設定
        self.thread_1_flag = True  # マウス読み取りスレッドのフラグ
        self.thread_2_flag = True  # オーディオ再生スレッドのフラグ
        self.thread_3_flag = True  # 終了スレッドのフラグ
        self.thread_1 = threading.Thread(target=self.read_mouse, args=(self.sensitivity, self.bias))
        self.thread_2 = threading.Thread(target=self.play_tone, args=(self.stream, self.volume, self.fs, self.sampling))
        
        # スレッド開始
        self.thread_1.start()
        self.thread_2.start()
        
        # 再生
        if endless == True:  # エンドレス再生
            print('Endress play. Press Enter to finish.')
            # キーボードでエンターキーを押したら終了
            while self.thread_3_flag:
                if input() == "":
                    self.finish()
                    self.thread_3_flag = False
        else:  # 指定時間再生
            print('Play ' + str(play_time_sec) + ' seconds')
            n = play_time_sec
            while n!=0:
                print('rest ' + str(n) + 'seconds')
                time.sleep(1)
                n -= 1
            self.finish()

        
    def finish(self):
        self.thread_1_flag = False
        self.thread_2_flag = False
        if hasattr(self, 'thread_1'):
            self.thread_1.join()
        if hasattr(self, 'thread_2'):
            self.thread_2.join()
        print('Finish playing')


    def read_mouse(self, sensitivity, bias):
        w_0, h_0 = pgui.position()
        w_th, h_th = pgui.size()
        
        while self.thread_1_flag:
            w_1, h_1 = pgui.position()
            move_len = math.sqrt((w_1 - w_0)**2 + (h_1 - h_0)**2)  # マウスが動いた距離
            self.move_len_track.append(move_len)
            #print('move_len: ' + str(round(move_len)))
            if move_len == 0:
                continue
            #print('MOVE')
            self.sound_freq = round(move_len*sensitivity + bias)  # スクラッチ音の周波数
            print('sound_freq = ' + str(self.sound_freq))
            w_0, h_0 = w_1, h_1
    

    def play_tone(self, stream, volume, fs, length):
        count = 0
        count2 = 0
        count2_th = 0.05  # マウスが止まったときのノイズ音を許容する時間(秒)
        count2_limit = count2_th / length
        sound_freq_old = self.sound_freq
        phaze_start = 0
        
        # オーディオを鳴らす
        while self.thread_2_flag:
            count2 = count2 + 1
            if self.sound_freq != sound_freq_old:
                count2 = 0
            else:
                if count2 > count2_limit:
                    continue
            chunks = []
            ret, phaze_last = self.make_time_varying_sine(sound_freq_old, self.sound_freq, volume, fs, length, phaze_start)
            chunks.append(ret)
            chunk = np.concatenate(chunks)
            self.chunk_plot.append(chunk)
            #print("sound_freq:" + str(sound_freq) + "sound_freq_old:" + str(sound_freq_old))
            sound_freq_old = self.sound_freq
            phaze_start = phaze_last
            stream.write(chunk.astype(np.float32).tobytes())
            count = count + 1
            
        #print("count:"+str(count))
    

    def make_time_varying_sine(self, start_freq, end_freq, volume, fs, sec, phaze_start):
        # 周波数が変化するsin波
        ## スイープ周波数
        freqs = np.linspace(start_freq, end_freq, num = int(round(fs * sec)))
        ## 角周波数の変化量
        phazes_diff = 2. * np.pi * freqs / fs
        ## 位相
        phazes = np.cumsum(phazes_diff) + phaze_start
        ## サイン波合成
        ret = volume * np.sin(phazes)
        phaze_last = phazes[-1]
        return ret, phaze_last
    

    def plot_tone(self, time_lim=(0,0)):
        x = np.arange(0, len(self.chunk_plot)*self.sampling, 1/self.fs)
        y = np.hstack(list(self.chunk_plot))
        plt.plot(x,y)
        if  time_lim != (0,0):
            plt.xlim(time_lim[0], time_lim[1])
        plt.rcParams['font.size']=16
        plt.ylabel('tone')
        plt.xlabel('time(sec)')
        plt.show()       


if __name__ == '__main__':

    #初期化
    dj = mouseDJ()
    
    #再生開始
    #例1) 5秒間再生
    dj.start(endless=False, play_time_sec=5)
    
    #例2) エンドレス再生
    #dj.start(endless=True)

    #スクラッチ音の波形をプロット
    #dj.plot_tone((0, 3)) #0秒から3秒の音をプロット
