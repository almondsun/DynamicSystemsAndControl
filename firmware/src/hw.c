/* hw.c - NUCLEO-L432KC peripherals for the Buck Rev C firmware.
 * See hw.h for the pin map. Safety design:
 *  - Outputs are written low before their pins become outputs.
 *  - TIM1 runs with OSSI = 1 and idle level low, so clearing MOE drives the
 *    PWM pin low at once (hw_pwm_off, fault handlers, debugger halt).
 *  - Any reset (watchdog included) returns PA8 to an input; R2 on the board
 *    then holds Q2 off, so Q1 is off by hardware.
 */
#include "hw.h"

#include "stm32l4xx_hal.h"
#include "stm32l4xx_ll_adc.h"

#define ADC_TIMEOUT_MS     2u
#define VDDA_AVG_SAMPLES   64u
#define UART_BAUD          115200u
#define UART_TX_TIMEOUT_MS 100u
#define RX_BUF_SIZE        128u
#define WDG_RELOAD         500u  /* LSI 32 kHz / 32 = 1 kHz -> 0.5 s */

static TIM_HandleTypeDef htim1;
static ADC_HandleTypeDef hadc1;
static UART_HandleTypeDef huart2;
static IWDG_HandleTypeDef hiwdg;

static volatile uint8_t rx_buf[RX_BUF_SIZE];
static volatile uint32_t rx_head;
static volatile uint32_t rx_tail;
static volatile bool pwm_tripped;
static volatile hw_sample_cb_t sample_cb;
static bool reset_by_watchdog;
static uint32_t vdda_mv;

/* Last resort: PWM low, loads off, wait for the watchdog. */
static void fatal(void)
{
    __disable_irq();
    TIM1->BDTR &= ~TIM_BDTR_MOE;
    GPIOA->BRR = GPIO_PIN_12 | GPIO_PIN_4;
    GPIOB->BRR = GPIO_PIN_0;
    for (;;) {
    }
}

void HardFault_Handler(void) { fatal(); }
void SysTick_Handler(void) { HAL_IncTick(); }

void USART2_IRQHandler(void)
{
    /* Any error flag (not all of them: __HAL_UART_GET_FLAG tests all-of). An
     * uncleared ORE keeps RXNEIE asserted and would starve the main loop. */
    if ((huart2.Instance->ISR & (USART_ISR_ORE | USART_ISR_FE | USART_ISR_NE | USART_ISR_PE)) != 0u) {
        huart2.Instance->ICR = USART_ICR_ORECF | USART_ICR_FECF | USART_ICR_NECF | USART_ICR_PECF;
    }
    if (__HAL_UART_GET_FLAG(&huart2, UART_FLAG_RXNE)) {
        const uint8_t c = (uint8_t)(huart2.Instance->RDR & 0xFFu);
        const uint32_t next = (rx_head + 1u) % RX_BUF_SIZE;
        if (next != rx_tail) { /* drop the byte when the buffer is full */
            rx_buf[rx_head] = c;
            rx_head = next;
        }
    }
}

/* Injected sequence done (VOUT rank 1, VIN rank 2), once per PWM period. */
void ADC1_IRQHandler(void)
{
    if ((ADC1->ISR & ADC_ISR_JEOS) == 0u) {
        return;
    }
    ADC1->ISR = ADC_ISR_JEOS | ADC_ISR_JEOC; /* write 1 to clear */
    const uint16_t vout_raw = (uint16_t)ADC1->JDR1;
    const uint16_t vin_raw = (uint16_t)ADC1->JDR2;
    const hw_sample_cb_t cb = sample_cb;
    if (cb != NULL) {
        cb(vout_raw, vin_raw);
    }
}

/* 80 MHz from MSI 4 MHz: VCO = 4 x 40 = 160 MHz, SYSCLK = VCO / 2. */
static void clock_init(void)
{
    __HAL_RCC_PWR_CLK_ENABLE();
    if (HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1) != HAL_OK) {
        fatal();
    }
    RCC_OscInitTypeDef osc = {0};
    osc.OscillatorType = RCC_OSCILLATORTYPE_MSI;
    osc.MSIState = RCC_MSI_ON;
    osc.MSICalibrationValue = RCC_MSICALIBRATION_DEFAULT;
    osc.MSIClockRange = RCC_MSIRANGE_6;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_MSI;
    osc.PLL.PLLM = 1;
    osc.PLL.PLLN = 40;
    osc.PLL.PLLP = RCC_PLLP_DIV7;
    osc.PLL.PLLQ = RCC_PLLQ_DIV2;
    osc.PLL.PLLR = RCC_PLLR_DIV2;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK) {
        fatal();
    }
    RCC_ClkInitTypeDef clk = {0};
    clk.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV1;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_4) != HAL_OK) {
        fatal();
    }
}

static void gpio_out_init(void)
{
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_12 | GPIO_PIN_4, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_RESET);

    GPIO_InitTypeDef g = {0};
    g.Mode = GPIO_MODE_OUTPUT_PP;
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_LOW;
    g.Pin = GPIO_PIN_12 | GPIO_PIN_4;
    HAL_GPIO_Init(GPIOA, &g);
    g.Pin = GPIO_PIN_0;
    HAL_GPIO_Init(GPIOB, &g);
}

static void pwm_init(void)
{
    __HAL_RCC_TIM1_CLK_ENABLE();
    htim1.Instance = TIM1;
    htim1.Init.Prescaler = 0;
    htim1.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim1.Init.Period = PWM_PERIOD_COUNTS - 1u;
    htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim1.Init.RepetitionCounter = 0;
    htim1.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    if (HAL_TIM_PWM_Init(&htim1) != HAL_OK) {
        fatal();
    }

    TIM_OC_InitTypeDef oc = {0};
    oc.OCMode = TIM_OCMODE_PWM1;
    oc.Pulse = 0; /* duty 0 at boot */
    oc.OCPolarity = TIM_OCPOLARITY_HIGH;
    oc.OCNPolarity = TIM_OCNPOLARITY_HIGH;
    oc.OCFastMode = TIM_OCFAST_DISABLE;
    oc.OCIdleState = TIM_OCIDLESTATE_RESET;
    oc.OCNIdleState = TIM_OCNIDLESTATE_RESET;
    if (HAL_TIM_PWM_ConfigChannel(&htim1, &oc, TIM_CHANNEL_1) != HAL_OK) {
        fatal();
    }

    TIM_BreakDeadTimeConfigTypeDef bd = {0};
    bd.OffStateRunMode = TIM_OSSR_DISABLE;
    bd.OffStateIDLEMode = TIM_OSSI_ENABLE; /* MOE = 0 -> pin driven to idle (low) */
    bd.LockLevel = TIM_LOCKLEVEL_OFF;
    bd.DeadTime = 0;
    bd.BreakState = TIM_BREAK_DISABLE;
    bd.BreakPolarity = TIM_BREAKPOLARITY_HIGH;
    bd.Break2State = TIM_BREAK2_DISABLE;
    bd.Break2Polarity = TIM_BREAK2POLARITY_HIGH;
    bd.AutomaticOutput = TIM_AUTOMATICOUTPUT_DISABLE;
    if (HAL_TIMEx_ConfigBreakDeadTime(&htim1, &bd) != HAL_OK) {
        fatal();
    }

    TIM_MasterConfigTypeDef master = {0};
    master.MasterOutputTrigger = TIM_TRGO_UPDATE; /* ADC trigger at each period start */
    master.MasterOutputTrigger2 = TIM_TRGO2_RESET;
    master.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
    if (HAL_TIMEx_MasterConfigSynchronization(&htim1, &master) != HAL_OK) {
        fatal();
    }

    if (HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1) != HAL_OK) {
        fatal();
    }
    __HAL_TIM_MOE_DISABLE_UNCONDITIONALLY(&htim1); /* stays low until the first duty */

    /* Pin to the timer only now, with the output already defined low. */
    GPIO_InitTypeDef g = {0};
    g.Pin = GPIO_PIN_8;
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_MEDIUM;
    g.Alternate = GPIO_AF1_TIM1;
    HAL_GPIO_Init(GPIOA, &g);
}

static uint32_t adc_read_raw(uint32_t channel, uint32_t sampling_time)
{
    ADC_ChannelConfTypeDef ch = {0};
    ch.Channel = channel;
    ch.Rank = ADC_REGULAR_RANK_1;
    ch.SamplingTime = sampling_time;
    ch.SingleDiff = ADC_SINGLE_ENDED;
    ch.OffsetNumber = ADC_OFFSET_NONE;
    ch.Offset = 0;
    if (HAL_ADC_ConfigChannel(&hadc1, &ch) != HAL_OK || HAL_ADC_Start(&hadc1) != HAL_OK ||
        HAL_ADC_PollForConversion(&hadc1, ADC_TIMEOUT_MS) != HAL_OK) {
        fatal();
    }
    return HAL_ADC_GetValue(&hadc1);
}

/* VDDA from VREFINT, regular group, once at boot (before triggered sampling). */
static uint32_t measure_vdda_mv(void)
{
    (void)adc_read_raw(ADC_CHANNEL_VREFINT, ADC_SAMPLETIME_247CYCLES_5); /* VREFINT start-up */
    HAL_Delay(1);
    uint32_t sum = 0u;
    for (uint32_t i = 0u; i < VDDA_AVG_SAMPLES; i++) {
        sum += adc_read_raw(ADC_CHANNEL_VREFINT, ADC_SAMPLETIME_247CYCLES_5);
    }
    const uint32_t raw = (sum + VDDA_AVG_SAMPLES / 2u) / VDDA_AVG_SAMPLES;
    return (raw == 0u) ? 3300u : (VREFINT_CAL_VREF * (uint32_t)*VREFINT_CAL_ADDR) / raw;
}

static void adc_init(void)
{
    RCC_PeriphCLKInitTypeDef pclk = {0};
    pclk.PeriphClockSelection = RCC_PERIPHCLK_ADC;
    pclk.AdcClockSelection = RCC_ADCCLKSOURCE_SYSCLK;
    if (HAL_RCCEx_PeriphCLKConfig(&pclk) != HAL_OK) {
        fatal();
    }
    __HAL_RCC_ADC_CLK_ENABLE();

    GPIO_InitTypeDef g = {0};
    g.Pin = GPIO_PIN_1 | GPIO_PIN_3;
    g.Mode = GPIO_MODE_ANALOG;
    g.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &g);

    hadc1.Instance = ADC1;
    hadc1.Init.ClockPrescaler = ADC_CLOCK_ASYNC_DIV4; /* 20 MHz */
    hadc1.Init.Resolution = ADC_RESOLUTION_12B;
    hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
    /* Must be ENABLE: with scan disabled the HAL builds a 1-conversion injected
     * sequence and silently drops rank 2 (VIN). Regular group stays at 1 conversion. */
    hadc1.Init.ScanConvMode = ADC_SCAN_ENABLE;
    hadc1.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
    hadc1.Init.LowPowerAutoWait = DISABLE;
    hadc1.Init.ContinuousConvMode = DISABLE;
    hadc1.Init.NbrOfConversion = 1;
    hadc1.Init.DiscontinuousConvMode = DISABLE;
    hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
    hadc1.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
    hadc1.Init.DMAContinuousRequests = DISABLE;
    hadc1.Init.Overrun = ADC_OVR_DATA_OVERWRITTEN;
    hadc1.Init.OversamplingMode = DISABLE;
    if (HAL_ADC_Init(&hadc1) != HAL_OK) {
        fatal();
    }
    if (HAL_ADCEx_Calibration_Start(&hadc1, ADC_SINGLE_ENDED) != HAL_OK) {
        fatal();
    }
    vdda_mv = measure_vdda_mv();
}

static void adc_injected_config(uint32_t channel, uint32_t rank)
{
    ADC_InjectionConfTypeDef inj = {0};
    inj.InjectedChannel = channel;
    inj.InjectedRank = rank;
    inj.InjectedSamplingTime = ADC_SAMPLETIME_92CYCLES_5; /* 4.6 us; the 4.7 nF pin cap holds the charge */
    inj.InjectedSingleDiff = ADC_SINGLE_ENDED;
    inj.InjectedOffsetNumber = ADC_OFFSET_NONE;
    inj.InjectedOffset = 0;
    inj.InjectedNbrOfConversion = 2;
    inj.InjectedDiscontinuousConvMode = DISABLE;
    inj.AutoInjectedConv = DISABLE;
    inj.QueueInjectedContext = DISABLE;
    inj.ExternalTrigInjecConv = ADC_EXTERNALTRIGINJEC_T1_TRGO;
    inj.ExternalTrigInjecConvEdge = ADC_EXTERNALTRIGINJECCONV_EDGE_RISING;
    inj.InjecOversamplingMode = DISABLE;
    if (HAL_ADCEx_InjectedConfigChannel(&hadc1, &inj) != HAL_OK) {
        fatal();
    }
}

void hw_start_sampling(hw_sample_cb_t cb)
{
    sample_cb = cb;
    adc_injected_config(ADC_CHANNEL_6, ADC_INJECTED_RANK_1); /* VOUT */
    adc_injected_config(ADC_CHANNEL_8, ADC_INJECTED_RANK_2); /* VIN */
    __HAL_ADC_CLEAR_FLAG(&hadc1, ADC_FLAG_JEOC | ADC_FLAG_JEOS);
    __HAL_ADC_ENABLE_IT(&hadc1, ADC_IT_JEOS);
    HAL_NVIC_SetPriority(ADC1_IRQn, 0, 0); /* control loop: highest priority */
    HAL_NVIC_EnableIRQ(ADC1_IRQn);
    if (HAL_ADCEx_InjectedStart(&hadc1) != HAL_OK) { /* waits for TIM1 TRGO */
        fatal();
    }
}

static void uart_init(void)
{
    __HAL_RCC_USART2_CLK_ENABLE();
    GPIO_InitTypeDef g = {0};
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = GPIO_PULLUP;
    g.Speed = GPIO_SPEED_FREQ_LOW;
    g.Pin = GPIO_PIN_2;
    g.Alternate = GPIO_AF7_USART2;
    HAL_GPIO_Init(GPIOA, &g);
    g.Pin = GPIO_PIN_15;
    g.Alternate = GPIO_AF3_USART2;
    HAL_GPIO_Init(GPIOA, &g);

    huart2.Instance = USART2;
    huart2.Init.BaudRate = UART_BAUD;
    huart2.Init.WordLength = UART_WORDLENGTH_8B;
    huart2.Init.StopBits = UART_STOPBITS_1;
    huart2.Init.Parity = UART_PARITY_NONE;
    huart2.Init.Mode = UART_MODE_TX_RX;
    huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart2.Init.OverSampling = UART_OVERSAMPLING_16;
    huart2.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
    huart2.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
    if (HAL_UART_Init(&huart2) != HAL_OK) {
        fatal();
    }
    __HAL_UART_ENABLE_IT(&huart2, UART_IT_RXNE);
    HAL_NVIC_SetPriority(USART2_IRQn, 5, 0);
    HAL_NVIC_EnableIRQ(USART2_IRQn);
}

static void iwdg_init(void)
{
    hiwdg.Instance = IWDG;
    hiwdg.Init.Prescaler = IWDG_PRESCALER_32;
    hiwdg.Init.Window = IWDG_WINDOW_DISABLE;
    hiwdg.Init.Reload = WDG_RELOAD;
    if (HAL_IWDG_Init(&hiwdg) != HAL_OK) {
        fatal();
    }
}

void hw_init(void)
{
    HAL_Init();
    reset_by_watchdog = __HAL_RCC_GET_FLAG(RCC_FLAG_IWDGRST) != 0u;
    __HAL_RCC_CLEAR_RESET_FLAGS();
    gpio_out_init();
    clock_init();
    pwm_init();
    adc_init();
    uart_init();
    __HAL_DBGMCU_FREEZE_TIM1(); /* debugger halt: TIM1 outputs disabled -> idle low */
    __HAL_DBGMCU_FREEZE_IWDG();
    iwdg_init();
}

bool hw_reset_was_watchdog(void) { return reset_by_watchdog; }
uint32_t hw_sysclk_hz(void) { return HAL_RCC_GetSysClockFreq(); }
uint32_t hw_vdda_mv(void) { return vdda_mv; }

void hw_pwm_set_counts(uint32_t counts)
{
    const uint32_t clamped = (counts > PWM_MAX_COUNTS) ? PWM_MAX_COUNTS : counts;
    const uint32_t key = hw_irq_lock(); /* a trip from the ADC ISR cannot slip in between */
    if (!pwm_tripped) {
        TIM1->CCR1 = clamped;
        if (clamped > 0u) {
            TIM1->BDTR |= TIM_BDTR_MOE;
        }
    }
    hw_irq_unlock(key);
}

uint32_t hw_pwm_counts(void) { return TIM1->CCR1; }

void hw_pwm_off(void)
{
    TIM1->BDTR &= ~TIM_BDTR_MOE; /* low now */
    TIM1->CCR1 = 0u;
    TIM1->EGR = TIM_EGR_UG;      /* load CCR1 = 0 into the active register */
}

void hw_pwm_trip(void)
{
    pwm_tripped = true;
    hw_pwm_off();
}

void hw_pwm_release(void) { pwm_tripped = false; }

void hw_load_set(load_sw_t sw, bool on)
{
    const GPIO_PinState state = on ? GPIO_PIN_SET : GPIO_PIN_RESET;
    if (sw == LOAD_SW_A) {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_12, state);
    } else {
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, state);
    }
}

bool hw_load_get(load_sw_t sw)
{
    return (sw == LOAD_SW_A) ? ((GPIOA->ODR & GPIO_PIN_12) != 0u) : ((GPIOB->ODR & GPIO_PIN_0) != 0u);
}

void hw_trig_set(bool on) { HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, on ? GPIO_PIN_SET : GPIO_PIN_RESET); }
bool hw_trig_get(void) { return (GPIOA->ODR & GPIO_PIN_4) != 0u; }

int hw_uart_getc(void)
{
    if (rx_tail == rx_head) {
        return -1;
    }
    const uint8_t c = rx_buf[rx_tail];
    rx_tail = (rx_tail + 1u) % RX_BUF_SIZE;
    return (int)c;
}

void hw_uart_write(const char *s, size_t n)
{
    if (n > 0u) {
        (void)HAL_UART_Transmit(&huart2, (uint8_t *)s, (uint16_t)n, UART_TX_TIMEOUT_MS);
    }
}

uint32_t hw_irq_lock(void)
{
    const uint32_t primask = __get_PRIMASK();
    __disable_irq();
    return primask;
}

void hw_irq_unlock(uint32_t primask) { __set_PRIMASK(primask); }
void hw_wdg_kick(void) { (void)HAL_IWDG_Refresh(&hiwdg); }
uint32_t hw_millis(void) { return HAL_GetTick(); }
