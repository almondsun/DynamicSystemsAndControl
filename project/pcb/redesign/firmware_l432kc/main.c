/* STM32L432KCU6 / NUCLEO-L432KC. Compile-only review prototype, never auto-arms.
 * ST CubeL4 1.18.1 HAL/CMSIS; no F103 register definitions are reused.
 */
#include "stm32l4xx_hal.h"
#include "runtime.h"
#include <math.h>

#ifndef BUCK_BOARD_REVIEWED
#define BUCK_BOARD_REVIEWED 0
#endif
#define PERIOD_COUNTS 8000u
static ADC_HandleTypeDef adc1;
static DMA_HandleTypeDef dma_adc1;
static TIM_HandleTypeDef tim1;
static UART_HandleTypeDef uart1;
static IWDG_HandleTypeDef watchdog;
static BuckRuntime control;
static volatile uint16_t adc_buffer[2];
static volatile uint32_t frames, last_frame, cycles_max;
static volatile uint16_t last_adc;
static volatile unsigned timer_ticks;
static volatile bool gpio_ready, feed_watchdog = true;
/* Bare-metal startup uses newlib constructor initialization without CRT startup files. */
void _init(void) {}
void _fini(void) {}

static void run_output(bool enabled)
{
    if (gpio_ready) GPIOB->BSRR = enabled ? GPIO_PIN_0 : (uint32_t)GPIO_PIN_0 << 16;
}
static bool fault_active(void) { return (GPIOB->IDR & GPIO_PIN_7) == 0; }
static void trip(void)
{
    run_output(false);
    TIM1->CCR1 = PERIOD_COUNTS;
    control.mode = BUCK_FAULT;
    feed_watchdog = false;
}
static void fatal(void)
{
    __disable_irq();
    run_output(false);
    for (;;) { /* An already-started watchdog resets; cold-start errors remain off. */ }
}
static void check(HAL_StatusTypeDef s) { if (s != HAL_OK) fatal(); }

static void clock_init(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clock = {0};
    __HAL_RCC_PWR_CLK_ENABLE();
    check(HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1));
    osc.OscillatorType = RCC_OSCILLATORTYPE_HSI | RCC_OSCILLATORTYPE_LSI;
    osc.HSIState = RCC_HSI_ON;
    osc.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    osc.LSIState = RCC_LSI_ON;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSI;
    osc.PLL.PLLM = 1;
    osc.PLL.PLLN = 10;
    osc.PLL.PLLP = RCC_PLLP_DIV7;
    osc.PLL.PLLQ = RCC_PLLQ_DIV2;
    osc.PLL.PLLR = RCC_PLLR_DIV2;
    check(HAL_RCC_OscConfig(&osc));
    clock.ClockType = RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK |
                      RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clock.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clock.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clock.APB1CLKDivider = RCC_HCLK_DIV1;
    clock.APB2CLKDivider = RCC_HCLK_DIV1;
    check(HAL_RCC_ClockConfig(&clock, FLASH_LATENCY_4));
    if (HAL_RCC_GetSysClockFreq() != 80000000u) fatal();
}

static void gpio_init(void)
{
    GPIO_InitTypeDef g = {0};
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    /* Load safe levels BEFORE switching pin modes. Board pull-down R5 holds RUN off at reset. */
    GPIOB->BSRR = (uint32_t)(GPIO_PIN_0 | GPIO_PIN_1) << 16;
    GPIOA->BSRR = GPIO_PIN_8;
    g.Pin = GPIO_PIN_0 | GPIO_PIN_1;
    g.Mode = GPIO_MODE_OUTPUT_PP; g.Pull = GPIO_NOPULL; g.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOB, &g);
    gpio_ready = true;
    g.Pin = GPIO_PIN_7; g.Mode = GPIO_MODE_IT_FALLING; g.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOB, &g); /* External R13 pulls to NUC_3V3. SB18 must be open. */
    HAL_NVIC_SetPriority(EXTI9_5_IRQn, 0, 0); HAL_NVIC_EnableIRQ(EXTI9_5_IRQn);
    g.Pin = GPIO_PIN_8; g.Mode = GPIO_MODE_AF_PP; g.Alternate = GPIO_AF1_TIM1;
    g.Speed = GPIO_SPEED_FREQ_HIGH; HAL_GPIO_Init(GPIOA, &g);
    g.Pin = GPIO_PIN_9 | GPIO_PIN_10; g.Alternate = GPIO_AF7_USART1;
    HAL_GPIO_Init(GPIOA, &g);
    g.Pin = GPIO_PIN_0; g.Mode = GPIO_MODE_ANALOG_ADC_CONTROL; g.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &g); /* ADC1_IN5. SB17 open; no ST-LINK MCO on PA0. */
}

static void uart_init(void)
{
    __HAL_RCC_USART1_CLK_ENABLE();
    uart1.Instance = USART1;
    uart1.Init.BaudRate = 115200;
    uart1.Init.WordLength = UART_WORDLENGTH_8B;
    uart1.Init.StopBits = UART_STOPBITS_1;
    uart1.Init.Parity = UART_PARITY_NONE;
    uart1.Init.Mode = UART_MODE_TX_RX;
    uart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    uart1.Init.OverSampling = UART_OVERSAMPLING_16;
    uart1.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
    uart1.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
    check(HAL_UART_Init(&uart1));
}

static void timer_init(void)
{
    TIM_OC_InitTypeDef channel = {0};
    TIM_MasterConfigTypeDef master = {0};
    TIM_BreakDeadTimeConfigTypeDef break_cfg = {0};
    __HAL_RCC_TIM1_CLK_ENABLE();
    tim1.Instance = TIM1;
    tim1.Init.Prescaler = 0;
    tim1.Init.CounterMode = TIM_COUNTERMODE_UP;
    tim1.Init.Period = PERIOD_COUNTS - 1;
    tim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    tim1.Init.RepetitionCounter = 0;
    tim1.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    check(HAL_TIM_PWM_Init(&tim1));
    channel.OCMode = TIM_OCMODE_PWM1;
    channel.Pulse = PERIOD_COUNTS; /* dprime=1: PA8 high; HCT14 output low; gate off. */
    channel.OCPolarity = TIM_OCPOLARITY_HIGH;
    channel.OCNPolarity = TIM_OCNPOLARITY_HIGH;
    channel.OCIdleState = TIM_OCIDLESTATE_SET;
    channel.OCNIdleState = TIM_OCNIDLESTATE_RESET;
    check(HAL_TIM_PWM_ConfigChannel(&tim1, &channel, TIM_CHANNEL_1));
    channel.OCMode = TIM_OCMODE_PWM2;
    channel.Pulse = PERIOD_COUNTS / 2;
    check(HAL_TIM_PWM_ConfigChannel(&tim1, &channel, TIM_CHANNEL_4));
    /* Regular ADC cannot use TIM1_CC4 directly on this MCU. TRGO2=OC4REF is supported. */
    master.MasterOutputTrigger = TIM_TRGO_RESET;
    master.MasterOutputTrigger2 = TIM_TRGO2_OC4REF;
    master.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
    check(HAL_TIMEx_MasterConfigSynchronization(&tim1, &master));
    break_cfg.OffStateRunMode = TIM_OSSR_ENABLE;
    break_cfg.OffStateIDLEMode = TIM_OSSI_ENABLE;
    break_cfg.LockLevel = TIM_LOCKLEVEL_OFF;
    break_cfg.BreakState = TIM_BREAK_DISABLE; /* PB7 is EXTI, NOT wired to BKIN. */
    break_cfg.Break2State = TIM_BREAK2_DISABLE;
    break_cfg.AutomaticOutput = TIM_AUTOMATICOUTPUT_DISABLE;
    check(HAL_TIMEx_ConfigBreakDeadTime(&tim1, &break_cfg));
    HAL_NVIC_SetPriority(TIM1_UP_TIM16_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(TIM1_UP_TIM16_IRQn);
}

static void adc_dma_init(void)
{
    ADC_ChannelConfTypeDef channel = {0};
    __HAL_RCC_ADC_CLK_ENABLE(); __HAL_RCC_DMA1_CLK_ENABLE();
    dma_adc1.Instance = DMA1_Channel1;
    dma_adc1.Init.Request = DMA_REQUEST_0;
    dma_adc1.Init.Direction = DMA_PERIPH_TO_MEMORY;
    dma_adc1.Init.PeriphInc = DMA_PINC_DISABLE;
    dma_adc1.Init.MemInc = DMA_MINC_ENABLE;
    dma_adc1.Init.PeriphDataAlignment = DMA_PDATAALIGN_HALFWORD;
    dma_adc1.Init.MemDataAlignment = DMA_MDATAALIGN_HALFWORD;
    dma_adc1.Init.Mode = DMA_CIRCULAR;
    dma_adc1.Init.Priority = DMA_PRIORITY_HIGH;
    check(HAL_DMA_Init(&dma_adc1));
    __HAL_LINKDMA(&adc1, DMA_Handle, dma_adc1);
    HAL_NVIC_SetPriority(DMA1_Channel1_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel1_IRQn);
    adc1.Instance = ADC1;
    adc1.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV4; /* 80/4 = 20MHz ADC */
    adc1.Init.Resolution = ADC_RESOLUTION_12B;
    adc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
    adc1.Init.ScanConvMode = ADC_SCAN_DISABLE;
    adc1.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
    adc1.Init.LowPowerAutoWait = DISABLE;
    adc1.Init.ContinuousConvMode = DISABLE;
    adc1.Init.NbrOfConversion = 1;
    adc1.Init.DiscontinuousConvMode = DISABLE;
    adc1.Init.ExternalTrigConv = ADC_EXTERNALTRIG_T1_TRGO2;
    adc1.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_RISING;
    adc1.Init.DMAContinuousRequests = ENABLE;
    adc1.Init.Overrun = ADC_OVR_DATA_PRESERVED;
    adc1.Init.OversamplingMode = DISABLE;
    check(HAL_ADC_Init(&adc1));
    channel.Channel = ADC_CHANNEL_5;
    channel.Rank = ADC_REGULAR_RANK_1;
    channel.SamplingTime = ADC_SAMPLETIME_247CYCLES_5;
    channel.SingleDiff = ADC_SINGLE_ENDED;
    channel.OffsetNumber = ADC_OFFSET_NONE;
    check(HAL_ADC_ConfigChannel(&adc1, &channel));
    check(HAL_ADCEx_Calibration_Start(&adc1, ADC_SINGLE_ENDED));
}

static void sample_ready(unsigned index)
{
    const uint32_t begin = DWT->CYCCNT;
    const uint16_t value = adc_buffer[index];
    last_adc = value;
    ++frames;
    float dp = runtime_tick(&control, value, true, fault_active());
    if (!isfinite(dp) || dp < 0 || dp > 1) { trip(); return; }
    if (control.mode == BUCK_OFF || control.mode == BUCK_FAULT) run_output(false);
    TIM1->CCR1 = (uint32_t)(dp * PERIOD_COUNTS + .5f); /* preloaded: next wrap */
    uint32_t used = DWT->CYCCNT - begin;
    if (used > cycles_max) cycles_max = used;
    if (used > 2000u) trip(); /* compile target only; benchmark this deadline in hardware */
    if (feed_watchdog) check(HAL_IWDG_Refresh(&watchdog));
}
void HAL_ADC_ConvHalfCpltCallback(ADC_HandleTypeDef *h) { if (h == &adc1) sample_ready(0); }
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *h) { if (h == &adc1) sample_ready(1); }
void HAL_ADC_ErrorCallback(ADC_HandleTypeDef *h) { (void)h; trip(); }
void HAL_GPIO_EXTI_Callback(uint16_t pin) { if (pin == GPIO_PIN_7) trip(); }
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *h)
{
    if (h != &tim1) return;
    if (timer_ticks++ > 0 && frames != last_frame + 1) trip();
    last_frame = frames;
}
void SysTick_Handler(void) { HAL_IncTick(); }
void DMA1_Channel1_IRQHandler(void) { HAL_DMA_IRQHandler(&dma_adc1); }
void TIM1_UP_TIM16_IRQHandler(void) { HAL_TIM_IRQHandler(&tim1); }
void EXTI9_5_IRQHandler(void) { HAL_GPIO_EXTI_IRQHandler(GPIO_PIN_7); }
void NMI_Handler(void) { fatal(); }
void HardFault_Handler(void) { fatal(); }
void MemManage_Handler(void) { fatal(); }
void BusFault_Handler(void) { fatal(); }
void UsageFault_Handler(void) { fatal(); }

static void uart_number(uint32_t n)
{
    char digits[10]; unsigned count = 0;
    do { digits[count++] = (char)('0' + n % 10); n /= 10; } while (n);
    while (count) check(HAL_UART_Transmit(&uart1, (uint8_t *)&digits[--count], 1, 100));
}
static void uart_text(const char *s)
{
    while (*s) check(HAL_UART_Transmit(&uart1, (const uint8_t *)s++, 1, 100));
}
static void command(char c)
{
    if (c == 'i') {
        uart_text("L432,locked="); uart_number(!BUCK_BOARD_REVIEWED);
        uart_text(",mode="); uart_number(control.mode);
        uart_text(",adc="); uart_number(last_adc);
        uart_text(",frames="); uart_number(frames);
        uart_text(",max_cycles="); uart_number(cycles_max); uart_text("\r\n");
        return;
    }
    if (c != 's' && c != 'r' && c != '5' && c != '6' && c != '7') return;
    __disable_irq();
    if (c == 's') { run_output(false); runtime_stop(&control); TIM1->CCR1 = PERIOD_COUNTS; }
    /* No startup/power is permitted in the review build. Clear/arm requires a reviewed board. */
    if (BUCK_BOARD_REVIEWED && c == 'r') {
        run_output(false); runtime_stop(&control);
        GPIOB->BSRR = GPIO_PIN_1;
        for (volatile unsigned i = 0; i < 800; ++i) __NOP();
        GPIOB->BSRR = (uint32_t)GPIO_PIN_1 << 16;
    }
    if (BUCK_BOARD_REVIEWED && frames > 10 && (c == '5' || c == '6' || c == '7')) {
        bool ok = feed_watchdog && runtime_start(&control, BUCK_CLOSED, (float)(c - '0'), fault_active());
        if (ok) run_output(true);
    }
    __enable_irq();
}

int main(void)
{
    HAL_Init(); clock_init(); gpio_init(); uart_init();
    runtime_init(&control); timer_init(); adc_dma_init();
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
    watchdog.Instance = IWDG;
    watchdog.Init.Prescaler = IWDG_PRESCALER_32;
    watchdog.Init.Reload = 31;
    watchdog.Init.Window = IWDG_WINDOW_DISABLE;
    check(HAL_IWDG_Init(&watchdog)); /* ~32ms at 32kHz LSI, tolerance must be measured */
    check(HAL_ADC_Start_DMA(&adc1, (uint32_t *)(uintptr_t)adc_buffer, 2));
    __HAL_TIM_CLEAR_FLAG(&tim1, TIM_FLAG_UPDATE);
    check(HAL_TIM_Base_Start_IT(&tim1));
    check(HAL_TIM_PWM_Start(&tim1, TIM_CHANNEL_4)); /* internal OC4REF, no GPIO output */
    check(HAL_TIM_PWM_Start(&tim1, TIM_CHANNEL_1));
    const char welcome[] = "L432 REVIEW BUILD: RUN locked OFF; USART1 D1/D0, not ST-LINK VCP.\r\n";
    check(HAL_UART_Transmit(&uart1, (const uint8_t *)welcome, sizeof welcome - 1, 100));
    for (;;) {
        uint8_t c;
        if (HAL_UART_Receive(&uart1, &c, 1, 1) == HAL_OK) command((char)c);
    }
}
