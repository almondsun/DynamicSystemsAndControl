/* STM32F103C8, 8 MHz HSE, 72 MHz core. Register offsets: ST RM0008.
 * No HAL, heap, RTOS, USB, or logging in the control interrupt.
 */
#include "runtime.h"
#include <stddef.h>
#define REG(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define RCC 0x40021000u
#define GPIOA 0x40010800u
#define GPIOB 0x40010c00u
#define TIM1 0x40012c00u
#define TIM3 0x40000400u
#define ADC1 0x40012400u
#define DMA1 0x40020000u
#define USART1 0x40013800u
#define IWDG 0x40003000u
static BuckRuntime control;
static volatile uint16_t adc[40];
static unsigned half;
static volatile uint32_t irq_cycles_max;
static volatile uint16_t last_adc;
static inline void irq_off(void) { __asm volatile("cpsid i" ::: "memory"); }
static inline void irq_on(void) { __asm volatile("cpsie i" ::: "memory"); }
static void wait_cycles(unsigned n) { while(n--) __asm volatile("nop"); }
static bool fault(void) { return !(REG(GPIOB+8)&(1u<<10)); }
static void run(bool enabled) { REG(GPIOB+0x10)=enabled?1u:1u<<16; }
static void tx(char c) { while(!(REG(USART1)&(1u<<7))) {} REG(USART1+4)=(unsigned char)c; }
static void text(const char *s) { while(*s) tx(*s++); }
static void number(uint32_t v) { char b[11];unsigned i=0;do { b[i++]=(char)('0'+v%10);v/=10;}while(v);while(i)tx(b[--i]); }
static void disable(void) { run(false); REG(TIM1+0x34)=7200; runtime_stop(&control); }

void TIM1_UP_IRQHandler(void)
{
    uint32_t begin=REG(0xe0001004u);
    REG(TIM1+0x10)=0;
    const uint32_t flags=REG(DMA1);
    const uint32_t expected=half?2u:4u;
    const bool fresh=(flags&14u)==expected;
    uint32_t sum=0;
    if(fresh) for(unsigned i=0;i<20;i++) sum+=adc[half*20+i];
    REG(DMA1+4)=15;
    half^=1u;
    last_adc=(uint16_t)((sum+10)/20);
    float dp=runtime_tick(&control,last_adc,fresh,fault());
    if(control.mode==BUCK_OFF || control.mode==BUCK_FAULT) run(false);
    /* OC1PE keeps this command pending until the NEXT 10 kHz update event. */
    REG(TIM1+0x34)=(uint32_t)(dp*7200+.5f);
    const uint32_t elapsed=REG(0xe0001004u)-begin;
    if(elapsed>irq_cycles_max) irq_cycles_max=elapsed;
    if(elapsed>6000) { run(false);control.mode=BUCK_FAULT; }
    if(fresh) REG(IWDG)=0xaaaa;
}

static void clock_init(void)
{
    REG(RCC)|=1u<<16;
    unsigned timeout=1000000;
    while(!(REG(RCC)&(1u<<17))) if(!--timeout) for(;;) {} /* RUN pull-down holds off. */
    REG(0x40022000u)=0x12; /* FLASH prefetch, 2 wait states at 72MHz. */
    REG(RCC+4)=(7u<<18)|(1u<<16)|(4u<<8)|(2u<<14); /* PLL x9, APB1 /2, ADC /6. */
    REG(RCC)|=1u<<24;
    timeout=1000000;
    while(!(REG(RCC)&(1u<<25))) if(!--timeout) for(;;) {}
    REG(RCC+4)|=2;
    while((REG(RCC+4)&12)!=8) {}
    REG(RCC+0x14)|=1; /* AHB DMA1 */
    REG(RCC+0x18)|=(1u<<0)|(1u<<2)|(1u<<3)|(1u<<9)|(1u<<11)|(1u<<14);
    REG(RCC+0x1c)|=1u<<1;
}
static void peripherals(void)
{
    run(false);REG(GPIOB+0x10)=1u<<17;
    REG(GPIOB)=(REG(GPIOB)&~0xffu)|0x22; /* PB0 RUN, PB1 latch reset, 2MHz PP. */
    REG(GPIOB+4)=(REG(GPIOB+4)&~(15u<<8))|(8u<<8); /* PB10 input pull-up */
    REG(GPIOB+0x10)=1u<<10;
    REG(GPIOA)&=~15u; /* PA0 analog input */
    REG(GPIOA+0x10)=1u<<8;
    REG(GPIOA+4)=(REG(GPIOA+4)&~0xfffu)|0x4bbu; /* PA8 TIM1, PA9 TX, PA10 RX */
    REG(USART1+8)=625; /* 72MHz / 115200 */
    REG(USART1+0x0c)=(1u<<13)|(1u<<3)|(1u<<2);
    REG(TIM1+0x28)=0; REG(TIM1+0x2c)=7199;
    REG(TIM1+0x34)=7200; /* dprime=1: high, gate off */
    REG(TIM1+0x18)=(6u<<4)|(1u<<3); /* PWM1, CCR1 preload */
    REG(TIM1+0x20)=1; REG(TIM1+0x44)=1u<<15; /* CC1E, MOE */
    REG(TIM1)=1u<<7; REG(TIM1+4)=1u<<4; /* ARR preload, TRGO=CEN */
    REG(TIM1+0x14)=1; REG(TIM1+0x10)=0;
    REG(TIM3+0x28)=0;REG(TIM3+0x2c)=359;
    REG(TIM3+4)=2u<<4;REG(TIM3+0x14)=1;
    REG(TIM3+0x24)=324; /* First ADC trigger 0.5us after common start. */
    REG(TIM3+8)=6; /* Slave trigger mode, ITR0=TIM1 TRGO (RM0008 table 86). */
    REG(ADC1+0x10)=2; /* channel 0: 13.5 ADC clock sampling cycles */
    REG(ADC1+0x2c)=0;REG(ADC1+0x34)=0; /* one regular conversion, channel 0 */
    REG(ADC1+8)=1;
    wait_cycles(10000);
    REG(ADC1+8)|=1u<<3;while(REG(ADC1+8)&(1u<<3)) {}
    REG(ADC1+8)|=1u<<2;while(REG(ADC1+8)&(1u<<2)) {}
    REG(DMA1+8)=0;
    REG(DMA1+0x0c)=40;
    REG(DMA1+0x10)=ADC1+0x4c;
    REG(DMA1+0x14)=(uint32_t)(uintptr_t)adc;
    REG(DMA1+4)=15;
    REG(DMA1+8)=(2u<<12)|(1u<<10)|(1u<<8)|(1u<<7)|(1u<<5)|1u;
    REG(ADC1+8)=(1u<<20)|(4u<<17)|(1u<<8)|1u; /* EXTTRIG TIM3_TRGO, DMA */
    REG(0xe000edfc)|=1u<<24; REG(0xe0001000u)|=1; REG(0xe0001004u)=0;
    REG(TIM1+0x0c)=1;
    REG(0xe000e100u)=1u<<25;
    REG(IWDG)=0x5555;REG(IWDG+4)=0;REG(IWDG+8)=63;
    while(REG(IWDG+0x0c)) {}
    REG(IWDG)=0xaaaa;REG(IWDG)=0xcccc; /* ~6.4ms typical, LSI tolerance applies */
    REG(TIM1)|=1; /* Synchronously starts TIM3. */
}
static bool clear_fault(void)
{
    run(false);
    REG(GPIOB+0x10)=2;wait_cycles(50);REG(GPIOB+0x10)=2u<<16;
    wait_cycles(50);
    return !fault();
}
static void command(char c)
{
    if(c=='i') {
        text("STATE,");number(control.mode);tx(',');number(fault());tx(',');
        number(REG(0xe0042000u)&0xfffu);tx(',');
        number(*(volatile uint16_t *)(uintptr_t)0x1ffff7e0u);tx(',');
        number(irq_cycles_max);tx(',');number(last_adc);text("\r\n");return;
    }
    if(c=='d') {
        irq_off();disable();bool busy=control.capture;irq_on();
        if(busy) {text("BUSY capture; retry d\r\n");return;}
        text("tick_100us,vo_mV,vref_mV,dprime_10000,mode\r\n");
        for(unsigned i=0;i<control.count;i++) {
            BuckSample s=control.samples[i];number(s.tick);tx(',');number(s.millivolts);tx(',');
            number(s.reference_mv);tx(',');number(s.dprime_10000);tx(',');number(s.flags);text("\r\n");
        }
        text("END\r\n");return;
    }
    if(c=='?') {text("s stop; r clear; a/b/c OL .5/.6/.4; 5/6/7 PI; v capture; d stop+dump; i status\r\nmax_irq_cycles=");number(irq_cycles_max);text("\r\n");return;}
    irq_off();
    bool ok=true;
    if(c=='s') disable();
    else if(c=='r') {disable();ok=clear_fault();if(!ok) control.mode=BUCK_FAULT;}
    else if(c=='v') ok=runtime_capture(&control);
    else {
        BuckMode mode=BUCK_OFF;float value=0;
        if(c=='a'||c=='b'||c=='c') {mode=BUCK_OPEN;value=c=='a'?.5f:c=='b'?.6f:.4f;}
        if(c=='5'||c=='6'||c=='7') {mode=BUCK_CLOSED;value=(float)(c-'0');}
        if(mode==BUCK_OFF) ok=false;
        else if(control.mode==mode && !fault()) {
            if(mode==BUCK_OPEN) control.open_dprime=value;else control.reference=value;
        } else {
            ok=runtime_start(&control,mode,value,fault());
            if(ok) run(true);
        }
    }
    irq_on();text(ok?"OK\r\n":"REJECT\r\n");
}
int main(void)
{
    clock_init();runtime_init(&control);peripherals();
    text("BUCK rev A: disabled. Verify lab interlocks before r, then a or 6.\r\n");
    for(;;) if(REG(USART1)&(1u<<5)) {
        char c=(char)REG(USART1+4);
        if(c!='\r' && c!='\n') command(c);
    }
}
void Default_Handler(void) {run(false);for(;;) {}}
extern uint32_t _estack,_sidata,_sdata,_edata,_sbss,_ebss;
void Reset_Handler(void)
{
    uint32_t *src=&_sidata;
    for(uint32_t *p=&_sdata;p<&_edata;) *p++=*src++;
    for(uint32_t *p=&_sbss;p<&_ebss;) *p++=0;
    main();Default_Handler();
}
typedef void (*Handler)(void);
__attribute__((section(".isr_vector"),used))
const Handler vectors[76]={
    [0]=(Handler)&_estack,[1]=Reset_Handler,
    [2 ... 15]=Default_Handler,[16 ... 40]=Default_Handler,
    [41]=TIM1_UP_IRQHandler,[42 ... 75]=Default_Handler
};
