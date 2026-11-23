/* control.h - per-PWM-period control for the Buck Rev C: PI voltage loop
 * (Entrega 3 design), protections, measurement filters and a capture buffer.
 *
 * control_on_sample() runs in the ADC interrupt at the PWM rate. Every other
 * function is called from the main loop.
 */
#ifndef CONTROL_H
#define CONTROL_H

#include <stdbool.h>
#include <stdint.h>

#define CONTROL_VREF_MIN_V      3.0f
#define CONTROL_VREF_MAX_V      7.5f
#define CONTROL_VREF_STEP_MAX_V 1.5f
#define CAPTURE_LEN             2000u /* samples, one per PWM period (100 ms) */
#define CAPTURE_PRE             200u  /* samples kept before the event (10 ms) */

typedef enum { TRIP_NONE = 0, TRIP_VOUT_HIGH, TRIP_VIN_HIGH, TRIP_VIN_LOW } trip_t;

typedef struct {
    uint16_t vref_mv;
    uint16_t vout_mv;
    uint16_t ccr; /* duty x PWM_PERIOD_COUNTS */
} capture_sample_t;

void control_init(uint32_t vdda_mv);
void control_on_sample(uint16_t vout_raw, uint16_t vin_raw);

bool control_is_closed(void);
/* Bumpless start: integrator = present duty, vref ramps from the present VOUT
 * to vref_target at 0.05 V/ms. False if VIN is too low (guard on). */
bool control_pi_start(float vref_target_v);
/* Leaves the loop; returns the duty (counts) now held by the open loop. */
uint32_t control_pi_stop(void);
void control_force_open(void);
/* Closed loop: immediate reference step (|step| <= 1.5 V), marks an event. */
bool control_vref_step(float vref_v);
void control_set_vref_target(float vref_v); /* used by the next start */
float control_vref_target(void);
float control_vref_now(void);
uint32_t control_duty_counts(void);
uint32_t control_sample_count(void); /* ADC interrupts since boot (rate check) */

float control_vout_v(void); /* filtered, tau ~ 13 ms */
float control_vin_v(void);
uint32_t control_vdda_mv(void);
float control_vout_cal(void);
bool control_calibrate_vout(float measured_v);
void control_set_vin_low_guard(bool on);
bool control_vin_low_guard(void);
trip_t control_take_trip(void); /* returns and clears the latched trip */

void control_mark_event(void);
bool control_capture_poll(void); /* true once when a new capture is ready */
uint32_t control_capture_count(void);
uint32_t control_capture_pre(void);
capture_sample_t control_capture_sample(uint32_t i);

#endif /* CONTROL_H */
