/* hw.h - NUCLEO-L432KC hardware layer for the Buck Rev C firmware.
 *
 * Pin map (BRINGUP_AND_TEST_GUIDE.md section 5):
 *   PA8  (D9)  TIM1_CH1  PWM, active high: high = Q1 on
 *   PA12 (D2)  GPIO      LSW_A, 1 = 36 R load connected (J3)
 *   PB0  (D3)  GPIO      LSW_B, 1 = 24 R load connected (J4)
 *   PA4  (A3)  GPIO      TRIG, scope marker (TP10)
 *   PA1  (A1)  ADC1_IN6  VOUT_SENSE = VOUT x 0.25
 *   PA3  (A2)  ADC1_IN8  VIN_SENSE  = VIN  x 0.25
 *   PA2/PA15   USART2    ST-LINK virtual COM port, 115200 8N1
 *
 * Sampling: TIM1 update (start of each PWM period) triggers the ADC injected
 * group (VOUT, VIN). Its end-of-sequence interrupt calls the sample callback,
 * which may write the next duty (CCR1 is preloaded: applies next period).
 */
#ifndef HW_H
#define HW_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define PWM_PERIOD_COUNTS 4000u /* 80 MHz timer clock / 4000 = 20 kHz */
#define PWM_MAX_COUNTS    3400u /* hard duty clamp: d <= 0.85 */

typedef enum { LOAD_SW_A, LOAD_SW_B } load_sw_t;
typedef void (*hw_sample_cb_t)(uint16_t vout_raw, uint16_t vin_raw);

/* Safe state: PWM output driven low, loads off, TRIG low, VDDA measured,
 * 0.5 s watchdog running. Sampling is not started yet. */
void hw_init(void);
/* Starts the TIM1-triggered ADC sampling; cb runs in the ADC interrupt. */
void hw_start_sampling(hw_sample_cb_t cb);
bool hw_reset_was_watchdog(void);
uint32_t hw_sysclk_hz(void);
uint32_t hw_vdda_mv(void);

/* Writes CCR1 (clamped to PWM_MAX_COUNTS); ignored while the PWM is tripped. */
void hw_pwm_set_counts(uint32_t counts);
uint32_t hw_pwm_counts(void);
/* Immediate stop: the output goes low now, without waiting for the period end. */
void hw_pwm_off(void);
/* Immediate stop that also blocks hw_pwm_set_counts until hw_pwm_release(). */
void hw_pwm_trip(void);
void hw_pwm_release(void);

void hw_load_set(load_sw_t sw, bool on);
bool hw_load_get(load_sw_t sw);
void hw_trig_set(bool on);
bool hw_trig_get(void);

int hw_uart_getc(void); /* -1 when no character is waiting */
void hw_uart_write(const char *s, size_t n);

uint32_t hw_irq_lock(void);          /* returns the previous PRIMASK */
void hw_irq_unlock(uint32_t primask);
void hw_wdg_kick(void);
uint32_t hw_millis(void);

#endif /* HW_H */
