"""
呼吸比为1：1，呼吸与心跳运动为频率0.15Hz到0.35Hz 与 1.2Hz
采样频率102.4Hz，采样时间40s，采样点数4096点
    5.8GHz：呼吸位移从6mm到16mm，心跳位移从4mm到14mm
    24GHz：呼吸位移从6mm到16mm，心跳位移从4mm到14mm
时域与频域图像
"""

import numpy as np
from numpy import fft as nf
from matplotlib import pyplot as plt

pi = np.pi
# 呼吸与心跳频率
f_respir = 0.26
f_heart = 1.2

# 4096点采样
var = 4
N = list(range(1024 * var))

# 采样频率102.4Hz
fs = 102.4
t = list(i / fs for i in N)

# 分辨频率与频率范围
f = fs / (1024 * var)

# 呼吸与心跳的最大频率取3Hz，即3/f个点
n = list(f * i for i in N)[0:121]


# 呼吸与心跳运动模拟
def respir_heart_move(d_respir, f_respir, d_heart, f_heart):
    x_respir = d_respir * np.sin(np.dot(f_respir * 2 * pi, t))
    x_heart = d_heart * np.sin(np.dot(f_heart * 2 * pi, t))
    # 经过上述计算，数据格式转化为np.array,使用 ‘+’ 代表对应元素相加
    respir_heart_move_ = x_respir + x_heart
    return respir_heart_move_


# 雷达输出信号模拟
def radar_output_signal(radar_element, respir_heart_move_):
    radar_output_signal_ = np.cos(np.dot(radar_element, respir_heart_move_) + 3 * pi / 2)
    return radar_output_signal_


# 呼吸次数从9次到21次，呼吸位移从6mm到16mm，心跳位移从4mm到14mm
for f_respir in np.arange(0.15, 0.36, 0.025):
    for d_respir in np.arange(0.003, 0.0081, 0.001):
        for d_heart in np.arange(0.0002, 0.00071, 0.0001):

            # 呼吸与心跳运动模拟
            respir_heart_move_ = respir_heart_move(d_respir, f_respir, d_heart, f_heart)

            # 5.8GHz & 24GHz雷达接受信号模拟
            radar_243 = radar_output_signal(243, respir_heart_move_)
            radar_1005 = radar_output_signal(1005, respir_heart_move_)

            # FFT 并 单边幅值谱
            y_1 = abs(nf.fft(radar_243, 1024 * var))[0:1024 * var // 2]
            y_2 = abs(nf.fft(radar_1005, 1024 * var))[0:1024 * var // 2]

            # # 绘图
            title_1 = 'Respiration '+str(round(60*f_respir, 2))+'pm_Heartbeat '+str(round(60*f_heart, 2))+'pm   '
            title_2 = 'Respiration '+str(round(2000*d_respir, 2))+'mm_Heartbeat '+str(round(2000*d_heart, 2))+'mm'
            plt.ion()
            plt.figure(figsize=(30, 15))
            # 呼吸与心跳原始波形图
            plt.subplot(511)
            plt.plot(t, respir_heart_move_)
            plt.title(title_1 + title_2 + '\n' + '\n' + 'Respiration and Heartbeat Movement')
            # 5.8GHz雷达信号时域图
            plt.subplot(512)
            plt.plot(t, radar_243)
            plt.title('Time domain diagram of 5.8GHz radar signal')
            # 5.8GHz雷达信号频域图
            plt.subplot(513)
            plt.plot(n, y_1[0:121])
            plt.title('Frequency domain diagram of 5.8GHz radar signal')
            # 24GHz雷达信号时域图
            plt.subplot(514)
            plt.plot(t, radar_1005)
            plt.title('Time domain diagram of 24GHz radar signal')
            # 24GHz雷达信号频域图
            plt.subplot(515)
            plt.plot(n, y_2[0:121])
            plt.title('Frequency domain diagram of 24GHz radar signal')
            plt.show()
            dir_name = 'E:/yuanhao_python_work/Bio_Radar/Simulation_/Simu1_Figure/'
            figure_name_1 = '呼吸' + str(round(60 * f_respir, 2)) + '次_心跳' + str(round(60 * f_heart, 2)) + '次_'
            figure_name_2 = '呼吸' + str(round(2000 * d_respir, 2)) + 'mm_心跳' + str(round(2000 * d_heart, 2)) + 'mm'
            filename = dir_name + figure_name_1 + figure_name_2 + '.png'
            plt.savefig(filename)
            plt.pause(0.8)
            plt.close()
