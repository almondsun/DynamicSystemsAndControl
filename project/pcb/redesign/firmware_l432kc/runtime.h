#ifndef BUCK_RUNTIME_H
#define BUCK_RUNTIME_H
#include "buck_control.h"
#include <stdint.h>
#define BUCK_CAPTURE_COUNT 512u
typedef enum { BUCK_OFF, BUCK_RAMP, BUCK_OPEN, BUCK_CLOSED, BUCK_FAULT } BuckMode;
typedef struct { uint32_t tick; uint16_t millivolts, reference_mv, dprime_10000, flags; } BuckSample;
typedef struct {
    BuckControl pi;
    BuckMode mode, requested;
    float reference, open_dprime, ramp_duty, adc_volts_per_count, adc_offset;
    float last_command, applied_command;
    uint32_t tick, ramp_ticks;
    uint16_t count, low_ticks;
    bool capture;
    BuckSample samples[BUCK_CAPTURE_COUNT];
} BuckRuntime;
void runtime_init(BuckRuntime *r);
bool runtime_start(BuckRuntime *r, BuckMode mode, float value, bool fault_pin);
void runtime_stop(BuckRuntime *r);
float runtime_tick(BuckRuntime *r, uint16_t mean_adc, bool fresh, bool fault_pin);
bool runtime_capture(BuckRuntime *r);
#endif
