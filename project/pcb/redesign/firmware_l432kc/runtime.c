#include "runtime.h"
#include "calibration.h"
#include <math.h>
/* Rev B: VOUT below half the reference for 2 ms in CLOSED mode (VIN below the IR2110
 * UVLO, interface disabled) is a fault, so the PI cannot wind up and restart at full duty. */
#define BUCK_COLLAPSE_TICKS 20u
void runtime_init(BuckRuntime *r)
{
    *r = (BuckRuntime){0};
    r->adc_volts_per_count = BUCK_ADC_VOLTS_PER_COUNT;
    r->adc_offset = BUCK_ADC_OFFSET_VOLTS;
    runtime_stop(r);
}
void runtime_stop(BuckRuntime *r)
{
    r->mode = BUCK_OFF;
    r->requested = BUCK_OFF;
    buck_reset(&r->pi);
    r->ramp_duty = 0;
    r->ramp_ticks = 0;
    r->low_ticks = 0;
    r->last_command = r->applied_command = 1;
}
bool runtime_start(BuckRuntime *r, BuckMode mode, float value, bool fault_pin)
{
    if (r->mode != BUCK_OFF || fault_pin || !isfinite(value) ||
        !isfinite(r->adc_volts_per_count) || r->adc_volts_per_count <= 0 ||
        !isfinite(r->adc_offset)) return false;
    if (mode == BUCK_OPEN && value != .4f && value != .5f && value != .6f) return false;
    if (mode == BUCK_CLOSED && value != 5 && value != 6 && value != 7) return false;
    if (mode != BUCK_OPEN && mode != BUCK_CLOSED) return false;
    r->reference = mode == BUCK_CLOSED ? value : 6;
    r->open_dprime = mode == BUCK_OPEN ? value : .5f;
    r->requested = mode;
    r->mode = BUCK_RAMP;
    return true;
}
bool runtime_capture(BuckRuntime *r)
{
    if (r->capture) return false;
    r->count = 0;
    r->capture = true;
    return true;
}
float runtime_tick(BuckRuntime *r, uint16_t mean_adc, bool fresh, bool fault_pin)
{
    const float v = mean_adc * r->adc_volts_per_count + r->adc_offset;
    float dp = 1;
    ++r->tick;
    if (!fresh || fault_pin || mean_adc >= 4095 || !isfinite(v) || v < -.1f || v > 8.3f)
        r->mode = BUCK_FAULT;
    if (r->mode == BUCK_RAMP) {
        const float target = r->requested == BUCK_OPEN ? 1-r->open_dprime : r->reference/12;
        r->ramp_duty += .0001f;
        if (++r->ramp_ticks > 12000) r->mode = BUCK_FAULT;
        else if (r->requested == BUCK_CLOSED && v >= r->reference-.1f) {
            r->pi.integral = r->ramp_duty-.5f-.026165528637673057f*(r->reference-v);
            r->mode = BUCK_CLOSED;
        } else if (r->requested == BUCK_OPEN && r->ramp_duty >= target) {
            r->ramp_duty = target;
            r->mode = BUCK_OPEN;
        }
        if (r->ramp_duty > .70f) r->ramp_duty = .70f;
        if (r->mode != BUCK_FAULT) dp = 1-r->ramp_duty;
    } else if (r->mode == BUCK_OPEN) dp = r->open_dprime;
    else if (r->mode == BUCK_CLOSED) {
        r->low_ticks = v < .5f * r->reference ? r->low_ticks + 1 : 0;
        dp = buck_update(&r->pi, v, r->reference, true);
        if (r->pi.fault || r->low_ticks > BUCK_COLLAPSE_TICKS) r->mode = BUCK_FAULT;
    }
    if (r->mode == BUCK_FAULT || r->mode == BUCK_OFF) dp = 1;
    if (r->capture) {
        r->samples[r->count++] = (BuckSample){r->tick,
            (uint16_t)(isfinite(v) && v >= 0 && v < 65 ? v*1000 : 65535),
            (uint16_t)(r->reference*1000), (uint16_t)(r->applied_command*10000), (uint16_t)r->mode};
        if (r->count == BUCK_CAPTURE_COUNT) r->capture = false;
    }
    r->applied_command = r->last_command;
    r->last_command = dp;
    return dp;
}
