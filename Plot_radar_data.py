"""
数据从雷达串口发出，由matlab接收，后由Python绘图并提取信息
"""
from numpy import fft as nf
from scipy.io import loadmat
from matplotlib import pyplot as plt
import os


def Readname(filepath):
    filepath_ = ''
    for i in filepath:
        # python本身使用 \ 来转义一些特殊字符，因此想要输出一个 \ ，得写两个 \
        if i != '\\':
            filepath_ = filepath_ + i
        else:
            filepath_ = filepath_ + '/'
    all_datafile_name = os.listdir(filepath_)
    return all_datafile_name


def Load_data(filename):
    radar_data = loadmat(filename)
    keys = radar_data.keys()
    keys = str(keys)
    data_key = ''

    # loadmat函数返回字典，数据存储在最后一个key中
    for i in range(-4, -1000, -1):
        if keys[i] == '\'':
            break
        data_key = keys[i] + data_key

    radar_data = radar_data[data_key]
    radar_data = radar_data[0]

    return radar_data


def Data_plot(time_queue, fre_queue, all_datafile_name):
    for datafile_name in all_datafile_name:
        filename = filepath + '/' + datafile_name

        # 防止加载非.mat文件
        if filename[-1] == 't':
            radar_data = Load_data(filename)
            # 由于直流分量的存在，导致0Hz处的幅值特别高需要排除
            y_1 = abs(nf.fft(radar_data, len(time_queue)))[1: 121]

            # 绘图
            plt.ion()
            plt.figure(figsize=(30, 20))

            if len(time_queue) == len(radar_data):
                # 画图----信号时域图
                plt.subplot(211)
                plt.plot(time_queue, radar_data)
                plt.title(datafile_name)
                # 画图----信号频域图
                plt.subplot(212)
                plt.plot(fre_queue, y_1)

                plt.show()

                dir_name = 'E:/yuanhao_python_work/Bio_Radar/Date_Process/Data_Plot/'
                filename = dir_name + datafile_name + '.png'
                plt.savefig(filename)
                plt.pause(1)
                print(filename)
        plt.close()


if __name__ == '__main__':
    filepath = input('复制粘贴文件夹地址: ')
    all_datafile_name = Readname(filepath)
    time_queue = [i / 102.4 for i in range(4096)]
    fre_queue = [i / 40 for i in range(1, 121)]
    Data_plot(time_queue, fre_queue, all_datafile_name)
