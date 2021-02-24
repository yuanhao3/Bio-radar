"""
呼吸比为respir_ratio，呼吸与心跳运动为频率0.15Hz到0.35Hz 与 1.2Hz
采样频率102.4Hz，采样时间40s，采样点数4096点
    5.8GHz：呼吸位移从6mm到16mm，心跳位移从4mm到14mm
    24GHz：呼吸位移从6mm到16mm，心跳位移从4mm到14mm
时域与频域图像
"""

import numpy as np
from numpy import fft as nf
from matplotlib import pyplot as plt

pi = np.pi
# 心跳频率固定为1.2Hz
f_heart = 1.2

# 4096点采样
var = 4
N = list(range(1024 * var))

# 采样频率102.4Hz
fs = 102.4
t = list(i / fs for i in N)

# 分辨频率与频率范围
f = fs / (1024 * var)
n = list(f * i for i in N)[0:121]

# 呼吸比
respir_ratio = 1.3


# 呼吸与心跳运动模拟
def respir_heart_move(d_respir, f_respir, d_heart, f_heart, N):
    # 吸气阶段频率与呼气阶段频率
    f_inspir = (respir_ratio+1) * f_respir / 2
    f_expir = (respir_ratio+1) * f_respir / (2*respir_ratio)

    # 吸气阶段频率与呼气阶段抽样点数
    N_inspir = int(0.5 * fs / f_inspir)
    N_expir = int(0.5 * fs / f_expir)
    N_respir = N_inspir + N_expir

    # 依据吸气与呼气时长构建吸气与呼吸所经历的时间序列
    t_inspir = t[0: N_inspir]
    t_expir = t[0: N_expir]

    # 一个周期内吸气与呼气各自所对应的运动模拟，并拼接
    x_inspir = d_respir * np.sin(np.dot(2 * pi * f_inspir, t_inspir) - pi / 2)
    x_expir = d_respir * np.sin(np.dot(2 * pi * f_expir, t_expir) + pi / 2)
    x_respir_one = np.hstack([x_inspir, x_expir])

    sample = 0
    x_respir = []
    while sample < N:
        # 将当前的呼吸周期置于前一个周期后
        x_respir = np.hstack([x_respir, x_respir_one])
        sample += N_respir

    # 当sample > 1024*var时，意味着上一个周期过后时长大于1024*var
    x_respir = x_respir[0: 1024*var]

    # 心跳运动模拟
    x_heart = d_heart * np.sin(np.dot(f_heart * 2 * pi, t))

    # 呼吸与心跳复合运动模拟，数据格式为np.array,使用 ‘+’ 代表对应元素相加
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
            respir_heart_move_ = respir_heart_move(d_respir, f_respir, d_heart, f_heart, len(N))

            # 5.8GHz & 24GHz雷达接受信号模拟
            radar_243 = radar_output_signal(243, respir_heart_move_)
            radar_1005 = radar_output_signal(1005, respir_heart_move_)

            # FFT 并 单边幅值谱
            y_1 = abs(nf.fft(radar_243, 1024 * var))[0:1024 * var // 2]
            y_2 = abs(nf.fft(radar_1005, 1024 * var))[0:1024 * var // 2]

            # # 绘图
            title_1 = 'Respiration '+str(round(60*f_respir, 2))+'pm_Heartbeat '+str(round(60*f_heart, 2))+'pm   '
            title_2 = 'Respiration '+str(round(2000*d_respir, 2))+'mm_Heartbeat '+str(round(2000*d_heart, 2))+'mm'
            # plt.ion()
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

            # plt.show()

            dir_name = 'E:/yuanhao_python_work/Bio_Radar/Simulation_/Simu2_Figure/'
            figure_name_0 = '呼吸比' + str(respir_ratio)
            figure_name_1 = '_呼吸' + str(round(60 * f_respir, 2)) + '次_心跳' + str(round(60 * f_heart, 2)) + '次_'
            figure_name_2 = '呼吸' + str(round(2000 * d_respir, 2)) + 'mm_心跳' + str(round(2000 * d_heart, 2)) + 'mm'
            filename = dir_name + figure_name_0 + figure_name_1 + figure_name_2 + '.png'

            plt.savefig(filename)
            # plt.pause(0.8)
            plt.close()