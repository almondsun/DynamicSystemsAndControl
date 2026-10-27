#include "buck_control.h"
#include <math.h>

void buck_reset(BuckControl *state)
{
    if (state) {
        state->integral = 0.0f;
        state->fault = false;
    }
}

float buck_update(BuckControl *state, float measured_volts,
                  float reference_volts, bool enabled)
{
    const float kp = 0.026165528637673057f;
    const float ki_ts = 0.007849658591301918f;
    if (!state) return 1.0f;
    if (!isfinite(measured_volts) || !isfinite(reference_volts) ||
        !isfinite(state->integral) || measured_volts < -0.1f ||
        measured_volts > 8.5f || reference_volts < 0.0f ||
        reference_volts > 7.0f) {
        state->fault = true;
    }
    if (!enabled || state->fault) {
        state->integral = 0.0f;
        return 1.0f;
    }
    const float error = reference_volts-measured_volts;
    const float raw = 0.5f+kp*error+state->integral;
    const float duty = fminf(0.95f, fmaxf(0.05f, raw));
    if (!((raw >= 0.95f && error > 0.0f) ||
          (raw <= 0.05f && error < 0.0f))) {
        state->integral += ki_ts*error;
    }
    return 1.0f-duty;
}
