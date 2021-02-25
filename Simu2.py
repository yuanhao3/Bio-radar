"""
呼吸比为1：1
采样频率102.4Hz，采样时间40s，采样点数4096点（可手动设置，Line16&Line20 取消注释即可）
5.8GHz 和 24GHz 的 时域与频域图像

为方便观察，程序绘出每一幅图像后1s自动关闭。
    注释掉Line132 160 169则不出图，仅自动保存，Line170请勿注释
    调整图像在屏幕停留时间，修改Line169参数即可
"""

import numpy as np
from numpy import fft as nf
from matplotlib import pyplot as plt

pi = np.pi
f_heart = 1.2  # 心跳频率固定为1.2Hz

# var = int(input('本程序作1024*N点的傅里叶变换，请输入采样周期：'))
var = 4  # 4096点采样
N = list(range(1024 * var))

# fs = int(input('请输入采样频率：'))
fs = 102.4  # 采样频率102.4Hz
t = list(i / fs for i in N)

f = fs / (1024 * var)  # 分辨频率
n = list(f * i for i in N)[0:121]  # 频率范围


# 呼吸与心跳运动模拟
def respir_heart_move(respir_ratio, d_respir, f_respir, d_heart, f_heart, N):
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


# 呼吸次数从9次到21次，呼吸位移从6mm到16mm，心跳位移从0.4mm到1.4mm
def data_input():
    # 在函数内部对函数外的变量进行操作，需要在函数内部声明其为global
    global data_input_label
    print('呼吸与心跳运动模拟为区间模拟，请按照提示依次输入重要模拟参数，建议依据真实情况输入正整数')
    # 呼吸比
    respir_ratio = float(input('请输入模拟呼吸运动的呼吸比：'))
    f_respir_start = float(input('请输入模拟呼吸运动在一分钟内的最小呼吸次数：'))
    f_respir_ending = float(input('请输入模拟呼吸运动在一分钟内的的最大呼吸次数：'))
    d_respir_start = float(input('请输入模拟呼吸运动可能引起的最小位移(mm)：'))
    d_respir_ending = float(input('请输入模拟呼吸运动可能引起的最大位移(mm)：'))
    d_heart_start = float(input('请输入模拟心跳运动可能引起的最小位移(mm)：'))
    d_heart_ending = float(input('请输入模拟心跳运动可能引起的最大位移(mm)：'))

    if f_respir_start > f_respir_ending or d_respir_start > d_respir_ending or d_heart_start > d_heart_ending:
        data_input_label = 'n'
        print('\n最大值不能小于最小值，请检查并重新输入\n')
    if f_respir_start <= f_respir_ending and d_respir_start <= d_respir_ending and d_heart_start <= d_heart_ending:
        print("请再次确认您的输入：")
        print("呼吸比:" + str(respir_ratio))
        print("最小呼吸次数：" + str(f_respir_start) + 'pm')
        print("最大呼吸次数：" + str(f_respir_ending) + 'pm')
        print("最小呼吸位移：" + str(d_respir_start) + 'mm')
        print("最大呼吸位移：" + str(d_respir_ending) + 'mm')
        print("最小心跳位移：" + str(d_heart_start) + 'mm')
        print("最大心跳位移：" + str(d_heart_ending) + 'mm')
        print('请输入 y 进行下一步，请输入 n 返回重新输入')
        # ######## global变量 需要在每一个if里都标明？
        data_input_label = input('y or n?: ')

    return respir_ratio, float(f_respir_start/60), float(f_respir_ending/60), float(d_respir_start/2000),\
       float(d_respir_ending/2000), float(d_heart_start/2000), float(d_heart_ending/2000), data_input_label


def respir_heart_Stimulate(respir_ratio, f_respir_start, f_respir_ending, d_respir_start, d_respir_ending,
                           d_heart_start, d_heart_ending):

    # 防止因首尾相等造成程序不运行
    for f_respir in np.arange(f_respir_start, f_respir_ending + 0.016, 1/30):
        for d_respir in np.arange(d_respir_start, d_respir_ending + 0.0001, 0.001):
            for d_heart in np.arange(d_heart_start, d_heart_ending + 0.00001, 0.0001):

                # 呼吸与心跳运动模拟
                respir_heart_move_ = respir_heart_move(respir_ratio, d_respir, f_respir, d_heart, f_heart, len(N))

                # 5.8GHz & 24GHz雷达接受信号模拟
                radar_243 = radar_output_signal(243, respir_heart_move_)
                radar_1005 = radar_output_signal(1005, respir_heart_move_)

                # FFT 并 单边幅值谱
                y_1 = abs(nf.fft(radar_243, 1024 * var))[0:1024 * var // 2]
                y_2 = abs(nf.fft(radar_1005, 1024 * var))[0:1024 * var // 2]

                # 绘图
                title_0 = 'Respir_ratio' + str(respir_ratio)
                title_1 = '    Respiration '+str(round(60*f_respir, 2))+'pm_Heartbeat '+str(round(60*f_heart, 2))+'pm   '
                title_2 = 'Respiration '+str(round(2000*d_respir, 2))+'mm_Heartbeat '+str(round(2000*d_heart, 2))+'mm'
                # plt.ion()
                plt.figure(figsize=(30, 15))

                # 呼吸与心跳原始波形图
                plt.subplot(511)
                plt.plot(t, respir_heart_move_)
                plt.title(title_0 + title_1 + title_2 + '\n' + '\n' + 'Respiration and Heartbeat Movement')

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
                # plt.pause(1)
                plt.close()


while True:
    respir_ratio, f_respir_start, f_respir_ending, d_respir_start, d_respir_ending, \
    d_heart_start, d_heart_ending, data_input_label = data_input()
    if data_input_label == 'y':
        respir_heart_Stimulate(respir_ratio, f_respir_start, f_respir_ending, d_respir_start, d_respir_ending,
                               d_heart_start, d_heart_ending)