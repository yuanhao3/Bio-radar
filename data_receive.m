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
        a=fread(s,1);
        str = char(a);
        if state ==1 
            data(cnt) = str;
            cnt=cnt+1
        end
        if str=='S'
            state = 1;
            count=count+1;
        elseif str=='P'
            state = 0;
            cnt = 1;
            i=1;
            break;
        end
        if (mod(cnt,80) == 0)
           for n=1:1:8
           y(i) = str2num(data((i-1)*10+1:(i-1)*10+8));
           %y1(i) = bitshift(y(i),-4);
           y1(i) = y(i)*3/4095;
           i=i+1;
           time=time+1;
           end
           if(i==9)
           figure(1);
           subplot(2,1,1);    
           x = ((time-8)*0.01:0.01:time*0.01-0.01);
           y2 = y1((i-8):(i-1));
           plot(x,y2,'r');
           xlim([(count-1)*10.24,count*10.24]);
           drawnow;
           hold on;
           end
           if(i~=9)
           x = ((time-9)*0.01:0.01:time*0.01-0.01);
           y2 = y1((i-9):(i-1));
           plot(x,y2,'r');drawnow;
           hold on;
           end
           if(i==1025)
           clf;
           radar_data(var*1024+1:var*1024+1024)=y1(1:1024);
           var=var+1;
           if(var==4)
           save('xxx','radar_data');
           var=0;
           t1=1:4096;
           subplot(2,1,2);
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
