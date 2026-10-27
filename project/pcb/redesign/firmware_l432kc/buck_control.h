#ifndef BUCK_CONTROL_H
#define BUCK_CONTROL_H
#include <stdbool.h>

/* SI units. Call once per 100 us. The adapter owns ADC calibration, PWM
 * timing, one-period update latency, and an independent hardware shutdown.
 * dprime=1 means MOSFET OFF only with the specified inverting driver.
 */
typedef struct {
    float integral;
    bool fault;
} BuckControl;

void buck_reset(BuckControl *state);
float buck_update(BuckControl *state, float measured_volts,
                  float reference_volts, bool enabled);
#endif
