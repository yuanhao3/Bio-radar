clc;
clear all;
delete(instrfindall); 
s = serial('com5');
set(s,'BaudRate',38400,'StopBits',1,'Parity','none','DataBits',8,'InputBufferSize',10240);
fopen(s);        
i=1;
time=1;
count=0;
var=0;
while(1)
    tic;
    state = 0;
    cnt=1;
    while(1)
        % 按位读取串口数据转为str
        a=fread(s,1);
        str = char(a);
        
        % DSP对连续波采样，每1024为一个周期，每周期数据以'S'为开始，'P'为结尾
        if str=='S'
            state = 1;
            count=count+1;
        elseif str=='P'
            state = 0;
            cnt = 1;
            i=1;
            break;
        end
        
        if state ==1 
            data(cnt) = str;
            cnt=cnt+1
        end
        
        % 每进行一次抽样，串口发送10位数据。取前8位用于转化为有效数据
        % 取2**3=8个抽样数据为一组进行集中转化
        if (mod(cnt,80) == 0)
           for n=1:1:8
               y(i) = str2num(data((i-1)*10+1:(i-1)*10+8));
               %y1(i) = bitshift(y(i),-4);
               y1(i) = y(i)*3/4095;
               i=i+1;
               time=time+1;
           end
           
           % 前8个抽样数据进行绘图
           if(i==9)
               figure(1);
               subplot(2,1,1);    
               x = ((time-8)*1/102.41/102.4:time*1/102.4-1/102.4);
               y2 = y1((i-8):(i-1));
               plot(x,y2,'r');
               xlim([(count-1)*10,count*10]);
               drawnow;
               hold on;
           end
           
           % 抽样数据进行绘图
           if(i~=9)
               x = ((time-9)*1/102.4:1/102.4:time*1/102.4-1/102.4);
               y2 = y1((i-9):(i-1));
               plot(x,y2,'r');
               drawnow;
               hold on;
           end
           
           % 每一个采样周期结束，将1024个抽样数据进行存储，4个周期存够4096个后保存为.mat文件，便于后续分析
           if(i==1025)
               clf;
               radar_data(var*1024+1:var*1024+1024)=y1(1:1024);
               var=var+1;
               if(var==4)
                   save('xxx','radar_data');
                   var=0;
                   
                   % 对4个周期内的所有数据进行绘图
                   subplot(2,1,2);
                   t1=1:4096;
                   plot(t1,radar_data);
                   drawnow;
                   hold on;
               end    
           end
        end
    toc;    
    end
end
fclose(s);
