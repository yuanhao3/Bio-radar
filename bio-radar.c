#include "DSP2833x_Device.h"     // DSP2833x Headerfile Include File
#include "DSP28x_Project.h"     // Device Headerfile and Examples Include File
#include <stdio.h>
#include <stdlib.h>
#include "math.h"
#include "fpu_rfft.h"

__interrupt void adc_isr(void);

#define Filter_N 50
#define RFFT_STAGES 10
#define RFFT_SIZE   (1 << RFFT_STAGES)
#define F_PER_SAMPLE (ADC_SAMPLINE_FREQ/(float)RFFT_SIZE)
#define Array_Full_Size  1
#define DAC_BUF_SIZE     512
#define DAC_Step         ((float)(0.60 * 21845) / DAC_BUF_SIZE)
#define SPI_Send(data)   {SpiaRegs.SPITXBUF = data;while(SpiaRegs.SPIFFTX.bit.TXFFST != 0);}
unsigned int DAC_SPI_Buf[DAC_BUF_SIZE * 2];
void InitSpiaGpio(void);
void start(void);
void spi_init(void);
//#define USE_TEST_INPUT 0

RFFT_ADC_F32_STRUCT rfft_adc;
RFFT_ADC_F32_STRUCT_Handle hnd_rfft_adc = &rfft_adc;

RFFT_F32_STRUCT rfft;
RFFT_F32_STRUCT_Handle hnd_rfft = &rfft;

volatile uint16_t flagInputReady = 0;
volatile uint16_t sampleIndex = 0;
volatile  unsigned int  Upload_Record_Complete_Flag = 0;

#pragma DATA_SECTION(RFFTin1Buff, "RFFTdata1");
uint16_t RFFTin1Buff[2*RFFT_SIZE];
uint16_t RFFTin2Buff[2*RFFT_SIZE];
#pragma DATA_SECTION(RFFToutBuff, "RFFTdata2");
float32 RFFToutBuff[RFFT_SIZE];
#pragma DATA_SECTION(RFFTmagBuff, "RFFTdata3");
float32 RFFTmagBuff[RFFT_SIZE/2+1];
#pragma DATA_SECTION(RFFTF32Coef, "RFFTdata4");
float32 RFFTF32Coef[RFFT_SIZE];

Uint16 Finding_The_Max_Index(float *p_Array, Uint16 i_first_index, Uint16 index_lengh);
void Float2Char(float Value,char *array);
void scib_echoback_init(void);
void InitScibGpio(void);
void scib_fifo_init(void);
void scib_xmit(int a);
void scib_msg(char * msg);
void ADCConfig(void);
void DACinit(void);
unsigned int i;
float filter_buf[Filter_N + 1] = {0};
float filter_sum = 0;
float real_range[Array_Full_Size] = {0.0};
int   index_record_array[Array_Full_Size] = {0};
int   index = 0;
int   n = 0;
float send_range;
float l=0;
float e=0;
float f1=0;
float f2=0;
float range=0;
char start_1 = 'S';
char stop_1 = 'P';
char msg[11];
extern Uint16 RamfuncsLoadStart;
extern Uint16 RamfuncsLoadEnd;
extern Uint16 RamfuncsRunStart;
extern Uint16 RamfuncsLoadSize;

void main(void)
{
   InitSysCtrl();
   memcpy(&RamfuncsRunStart, &RamfuncsLoadStart, (Uint32)&RamfuncsLoadSize);
   InitFlash();
   start();
   EALLOW;
   GpioCtrlRegs.GPAMUX1.bit.GPIO7 = 0;
   GpioCtrlRegs.GPADIR.bit.GPIO7 = 1;
   EDIS;
   GpioDataRegs.GPADAT.bit.GPIO7 = 0;
   start();
   EALLOW;
#define ADC_MODCLK 0x3 // HSPCLK = SYSCLKOUT/2*ADC_MODCLK2 = 150/(2*3)   = 25.0 MHz
   EDIS;
   EALLOW;
   SysCtrlRegs.HISPCP.all = ADC_MODCLK;
   EDIS;
   //InitGpio();  // Skipped for this example
   DINT;
   InitPieCtrl();
   IER = 0x0000;
   IFR = 0x0000;
   InitPieVectTable();
   spi_init();
   EnableInterrupts();     /*全局中断使能*/
   RD_int();
   PLL_int();
   ADCConfig();
   InitScibGpio();
   scib_echoback_init();
   scib_fifo_init();
   hnd_rfft_adc->Tail = &(hnd_rfft->OutBuf);
   hnd_rfft->FFTSize = RFFT_SIZE;
   hnd_rfft->FFTStages = RFFT_STAGES;
   hnd_rfft_adc->InBuf = &RFFTin1Buff[0];
   hnd_rfft->OutBuf    = &RFFToutBuff[0];
   hnd_rfft->CosSinBuf = &RFFTF32Coef[0];
   hnd_rfft->MagBuf    = &RFFTmagBuff[0];
   RFFT_f32_sincostable(hnd_rfft);
   while(1)
   {
      while(flagInputReady == 0){};
      hnd_rfft_adc->InBuf = &RFFTin1Buff[0];
      //RFFT_adc_f32(hnd_rfft_adc);
      hnd_rfft_adc->InBuf = &RFFTin2Buff[0];
      //RFFT_adc_f32(hnd_rfft_adc);
      flagInputReady = 0;
      sampleIndex =0;
   }
}

__interrupt void  adc_isr(void)
{
    static unsigned int i_DAC_count = 1;
        SPI_Send(DAC_SPI_Buf[i_DAC_count]);
        if(i_DAC_count == DAC_BUF_SIZE * 2 - 1)
        {
            i_DAC_count = 1;
        }
        else
        {
            i_DAC_count++;
        }
    if (sampleIndex==0)
           {
                 scib_xmit(start_1);
          }
    if(sampleIndex < RFFT_SIZE)
    {
    RFFTin1Buff[sampleIndex] = AdcRegs.ADCRESULT0;
    RFFTin2Buff[sampleIndex++] = AdcRegs.ADCRESULT1;
    //RFFTin1Buff[sampleIndex] = (AdcRegs.ADCRESULT0)*(0.54-0.46*cos(0.006*sampleIndex));   //哈明窗
    //RFFTin2Buff[sampleIndex++] = (AdcRegs.ADCRESULT1)*(0.54-0.46*cos(0.006*sampleIndex)); //哈明窗
    send_range = RFFTin1Buff[sampleIndex - 1];
    Float2Char(send_range,msg);
    scib_msg(msg);
     }
    else if(sampleIndex == RFFT_SIZE)
    {
        scib_xmit(stop_1);
        flagInputReady = 1;
    }
  AdcRegs.ADCTRL2.bit.RST_SEQ1 = 1;         // Reset SEQ1
  AdcRegs.ADCST.bit.INT_SEQ1_CLR = 1;       // Clear INT SEQ1 bit
  PieCtrlRegs.PIEACK.all = PIEACK_GROUP1;   // Acknowledge interrupt to PIE
  return;
}

void ADCConfig(void)
{
   EALLOW;  // This is needed to write to EALLOW protected register
   PieVectTable.ADCINT = &adc_isr;
   EDIS;    // This is needed to disable write to EALLOW protected registers

   InitAdc();  // For this example, init the ADC

   PieCtrlRegs.PIEIER1.bit.INTx6 = 1;
   IER |= M_INT1; // Enable CPU Interrupt 1
      EINT;          // Enable Global interrupt INTM
      ERTM;          // Enable Global realtime interrupt DBGM
      AdcRegs.ADCMAXCONV.all = 0x0001;       // Setup 2 conv's on SEQ1
      AdcRegs.ADCCHSELSEQ1.bit.CONV00 = 0x0; // Setup ADCINA3 as 1st SEQ1 conv.
      AdcRegs.ADCCHSELSEQ1.bit.CONV01 = 0x1; // Setup ADCINA3 as 1st SEQ1 conv.
      AdcRegs.ADCTRL2.bit.EPWM_SOCA_SEQ1 = 1;// Enable SOCA from ePWM to start SEQ1
      AdcRegs.ADCTRL2.bit.INT_ENA_SEQ1 = 1;  // Enable SEQ1 interrupt (every EOS)

      EPwm1Regs.ETSEL.bit.SOCAEN = 1;        // Enable SOC on A group
      EPwm1Regs.ETSEL.bit.SOCASEL = 4;       // Select SOC from from CPMA on upcount
      EPwm1Regs.ETPS.bit.SOCAPRD = 1;        // Generate pulse on 1st event
      EPwm1Regs.CMPA.half.CMPA = 0x0080;     // Set compare A value
      EPwm1Regs.TBPRD = 1907;              // Set period for ePWM1
      EPwm1Regs.TBCTL.bit.HSPCLKDIV = 6;       // count up and start
      EPwm1Regs.TBCTL.bit.CLKDIV = 6;       // count up and start
      EPwm1Regs.TBCTL.bit.CTRMODE = 0;       // count up and start
}


Uint16 Finding_The_Max_Index(float *p_Array, Uint16 i_first_index, Uint16 index_lengh)
{
   Uint16 k = 0, max_index = 0;
   float Max_Index_Value = 0;
   max_index=i_first_index;
   Max_Index_Value = *(p_Array + i_first_index);
   for (k = (i_first_index + 1); k < index_lengh; k++)
   {
    if (Max_Index_Value < *(p_Array + k))
      {
           Max_Index_Value = *(p_Array + k);
           max_index = k;
      }
   }

   return  max_index;
}

void scib_fifo_init()
{
    ScibRegs.SCIFFTX.all = 0xE040;
    ScibRegs.SCIFFRX.all = 0x204f;
    ScibRegs.SCIFFCT.all = 0x0;
}

void InitScibGpio()
{
    EALLOW;
    GpioCtrlRegs.GPAPUD.bit.GPIO9 = 0;
    GpioCtrlRegs.GPAPUD.bit.GPIO11 = 0;
    GpioCtrlRegs.GPAQSEL1.bit.GPIO9 = 3;
    GpioCtrlRegs.GPAQSEL1.bit.GPIO11 = 3;
    GpioCtrlRegs.GPAMUX1.bit.GPIO9 = 2;
    GpioCtrlRegs.GPAMUX1.bit.GPIO11 = 2;
    EDIS;
}

void scib_echoback_init()
{
    ScibRegs.SCICCR.all = 0x0007;
    ScibRegs.SCICTL1.all = 0x0003;
    ScibRegs.SCICTL2.all = 0x0003;
    ScibRegs.SCICTL2.bit.TXINTENA = 1;
    ScibRegs.SCICTL2.bit.RXBKINTENA = 1;
    ScibRegs.SCIHBAUD = 0x0000;
    ScibRegs.SCILBAUD = 0x0079;
    ScibRegs.SCICTL1.all = 0x0023;
}

void scib_msg(char * msg)
{
    int i;
    i = 0;
    while(msg[i]!='\n')
    {
        scib_xmit(msg[i]);
        i++;
    }
}

void scib_xmit(int a)
        {
           while (ScibRegs.SCIFFTX.bit.TXFFST!=0)
            {}
            ScibRegs.SCITXBUF = a;
        }

void Float2Char(float Value,char *array)
{
Uint16 IntegerPart;
float DecimalPart;
i=4;
msg[0]=48;
msg[1]=48;
msg[5]='.';
array[2]= 48;
array[3]= 48;
if (Value>=1)
    {
IntegerPart = (Uint16)Value;
DecimalPart = Value-IntegerPart;
    }
else
{
IntegerPart = 0;
DecimalPart = Value-IntegerPart;
    }
//转换整数部分
if (IntegerPart == 0)
    {
array[4] = 0+48;
}
else
{
while(IntegerPart>0)
    {
array[i] = IntegerPart%10+48;
IntegerPart = IntegerPart/10;
i--;
}
}
array[6] = (Uint16)(DecimalPart*10)%10+48;
array[7] = (Uint16)(DecimalPart*100)%10+48;
array[8] = 'm';
array[9] = 0x0D;
array[10] = '\n';
}

void start(void)
{
    EALLOW;
    GpioCtrlRegs.GPAPUD.bit.GPIO16 = 0;   // Enable pull-up on GPIO16 (SPISIMOA)
    GpioCtrlRegs.GPAPUD.bit.GPIO17 = 0;   // Enable pull-up on GPIO17 (SPISOMIA)
    GpioCtrlRegs.GPAPUD.bit.GPIO18 = 0;   // Enable pull-up on GPIO18 (SPICLKA)
    GpioCtrlRegs.GPAPUD.bit.GPIO19 = 0;   // Enable pull-up on GPIO19 (SPISTEA)

    GpioCtrlRegs.GPAQSEL2.bit.GPIO16 = 3; // Asynch input GPIO16 (SPISIMOA)
    GpioCtrlRegs.GPAQSEL2.bit.GPIO17 = 3; // Asynch input GPIO17 (SPISOMIA)
    GpioCtrlRegs.GPAQSEL2.bit.GPIO18 = 3; // Asynch input GPIO18 (SPICLKA)
    GpioCtrlRegs.GPAQSEL2.bit.GPIO19 = 3; // Asynch input GPIO19 (SPISTEA)

    GpioCtrlRegs.GPAMUX2.bit.GPIO16 = 1; // Configure GPIO16 as SPISIMOA
    GpioCtrlRegs.GPAMUX2.bit.GPIO17 = 1; // Configure GPIO17 as SPISOMIA
    GpioCtrlRegs.GPAMUX2.bit.GPIO18 = 1; // Configure GPIO18 as SPICLKA
    GpioCtrlRegs.GPAMUX2.bit.GPIO19 = 1; // Configure GPIO19 as SPISTEA
    EDIS;
}

void InitSpiaGpio(void)
{
    EALLOW;
//    GpioCtrlRegs.GPBDIR.bit.GPIO48 = 1;
//    GpioCtrlRegs.GPBDIR.bit.GPIO49 = 1;
//    GpioCtrlRegs.GPBDIR.bit.GPIO52 = 1;
    GpioCtrlRegs.GPADIR.bit.GPIO12 = 1;
    GpioCtrlRegs.GPADIR.bit.GPIO7 = 1;
    EDIS;
//    GpioDataRegs.GPBDAT.bit.GPIO48 = 1;
//    GpioDataRegs.GPBDAT.bit.GPIO49 = 0;
//    GpioDataRegs.GPBDAT.bit.GPIO52 = 0;
    GpioDataRegs.GPADAT.bit.GPIO12 = 1;
    GpioDataRegs.GPADAT.bit.GPIO7 = 0;
    EALLOW;
    GpioCtrlRegs.GPAPUD.bit.GPIO16 = 0;   // Enable pull-up on GPIO16 (SPISIMOA)
    GpioCtrlRegs.GPAPUD.bit.GPIO17 = 0;   // Enable pull-up on GPIO17 (SPISOMIA)
    GpioCtrlRegs.GPAPUD.bit.GPIO18 = 0;   // Enable pull-up on GPIO18 (SPICLKA)
    GpioCtrlRegs.GPAPUD.bit.GPIO19 = 0;   // Enable pull-up on GPIO19 (SPISTEA)

    GpioCtrlRegs.GPAQSEL2.bit.GPIO16 = 3; // Asynch input GPIO16 (SPISIMOA)
    GpioCtrlRegs.GPAQSEL2.bit.GPIO17 = 3; // Asynch input GPIO17 (SPISOMIA)
    GpioCtrlRegs.GPAQSEL2.bit.GPIO18 = 3; // Asynch input GPIO18 (SPICLKA)
    GpioCtrlRegs.GPAQSEL2.bit.GPIO19 = 3; // Asynch input GPIO19 (SPISTEA)

    GpioCtrlRegs.GPAMUX2.bit.GPIO16 = 1; // Configure GPIO16 as SPISIMOA
    GpioCtrlRegs.GPAMUX2.bit.GPIO17 = 1; // Configure GPIO17 as SPISOMIA
    GpioCtrlRegs.GPAMUX2.bit.GPIO18 = 1; // Configure GPIO18 as SPICLKA
    GpioCtrlRegs.GPAMUX2.bit.GPIO19 = 1; // Configure GPIO19 as SPISTEA
    EDIS;
}

//SPI功能初始化
void spi_init(void)
{
    SpiaRegs.SPIFFTX.all = 0xE040;
    SpiaRegs.SPIFFRX.all = 0x204f;
    SpiaRegs.SPIFFCT.all = 0x0;             //以上三行表示没有使用FIFO功能//

    SpiaRegs.SPICCR.all = 0x000F;           //复位，上升沿，16位数据长度//
    SpiaRegs.SPICTL.all = 0x000E;           //主设备，有相位延时，因此采用第四种时钟模式//
                                            //使能发送，禁止SPI中断//
    SpiaRegs.SPIBRR = 18;                   //18=0x0012，SPI波特率=LSPCLK/（SPIBRR+1）
                                            //=低速时钟/19,此时为对系统时钟4分频，因此波特率=9375000
    SpiaRegs.SPICCR.all = 0x008F;           //从复位模式恢复，禁止自测模式
    SpiaRegs.SPIPRI.bit.FREE = 1;           //不受断点的影响
}
void RD_int(void)
{
    DELAY_US(10);
    EALLOW;
    GpioCtrlRegs.GPADIR.bit.GPIO12 = 1;
    EDIS;
    GpioDataRegs.GPADAT.bit.GPIO12 = 1;
    DELAY_US(20);
    GpioDataRegs.GPADAT.bit.GPIO12 = 0;
    DELAY_US(500000);
    SPI_Send(0x0018);
    DELAY_US(500000);
    GpioDataRegs.GPADAT.bit.GPIO12 = 1;
    DELAY_US(20);
}

void PLL_int(void)
{
    EALLOW;
    GpioCtrlRegs.GPAMUX1.bit.GPIO13 = 0;
    GpioCtrlRegs.GPADIR.bit.GPIO13 = 1;
    GpioCtrlRegs.GPAMUX2.bit.GPIO19 = 0;
    GpioCtrlRegs.GPADIR.bit.GPIO19 = 1;
    EDIS;
    GpioDataRegs.GPADAT.bit.GPIO19 = 1;
    DELAY_US(20);
    GpioDataRegs.GPADAT.bit.GPIO7 = 1;
    DELAY_US(20);
    GpioDataRegs.GPADAT.bit.GPIO13 = 0;
    DELAY_US(20);
    GpioDataRegs.GPADAT.bit.GPIO19 = 0;
    SPI_Send(0x0000);  //R7
    SPI_Send(0x0007);  //R7
    GpioDataRegs.GPADAT.bit.GPIO19 = 1;
    DELAY_US(500);
    GpioDataRegs.GPADAT.bit.GPIO19 = 0;
    SPI_Send(0x0000);  //R6 (1)
    SPI_Send(0x0006);  //R6 (1)
    GpioDataRegs.GPADAT.bit.GPIO19 = 1;
    DELAY_US(500);
    GpioDataRegs.GPADAT.bit.GPIO19 = 0;
    SPI_Send(0x0080);  //R6 (2)
    SPI_Send(0x0006);  //R6 (2)
    GpioDataRegs.GPADAT.bit.GPIO19 = 1;
    DELAY_US(500)
    GpioDataRegs.GPADAT.bit.GPIO19 = 0;
    SPI_Send(0x0400);  //R5 (1)
    SPI_Send(0x0005);  //R5 (1)
    GpioDataRegs.GPADAT.bit.GPIO19 = 1;
    DELAY_US(500);
    GpioDataRegs.GPADAT.bit.GPIO19 = 0;
    SPI_Send(0x0480);  //R5 (1)
    SPI_Send(0x0005);  //R5 (1)
    GpioDataRegs.GPADAT.bit.GPIO19 = 1;
    DELAY_US(500);
    GpioDataRegs.GPADAT.bit.GPIO19 = 0;
    SPI_Send(0x0040);  //R4 (2)
    SPI_Send(0x0004);  //R4 (2)
    GpioDataRegs.GPADAT.bit.GPIO19 = 1;
    DELAY_US(500);
    GpioDataRegs.GPADAT.bit.GPIO19 = 0;
    SPI_Send(0x0000);  //R3
    SPI_Send(0x8043);  //R3
    GpioDataRegs.GPADAT.bit.GPIO19 = 1;
    DELAY_US(500);
    GpioDataRegs.GPADAT.bit.GPIO19 = 0;
    SPI_Send(0x0700);  //R2
    SPI_Send(0x8002);  //R2
    GpioDataRegs.GPADAT.bit.GPIO19 = 1;
    DELAY_US(500);
    GpioDataRegs.GPADAT.bit.GPIO19 = 0;
    SPI_Send(0x0000);  //R1
    SPI_Send(0x0001);  //R1
    GpioDataRegs.GPADAT.bit.GPIO19 = 1;
    DELAY_US(500);
    GpioDataRegs.GPADAT.bit.GPIO19 = 0;
    SPI_Send(0x0019);  //R0
    SPI_Send(0x0000);  //R0
    GpioDataRegs.GPADAT.bit.GPIO19 = 1;
    DELAY_US(500);
}
