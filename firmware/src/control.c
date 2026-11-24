/* control.c - see control.h.
 *
 * PI exactly as in the Entrega 3 model (analisis/entrega-3/matlab/e3_sim.m):
 *   e = vref - vout          (vout = ADC reading referred to VOUT, volts)
 *   In = I + KiTs*e; u = Kp*e + In
 *   conditional integration: keep I when u is beyond a limit and e pushes further
 *   d = clamp(u, 0, 0.85), written to the preloaded CCR -> applied next period
 * The ADC is sampled at the start of each period (TIM1 update), so the loop has
 * the 1.5 Ts delay of the design model.
 */
#include "control.h"

#include "hw.h"

#define KP              0.030477f
#define KI_TS           0.0045716f /* Ki = 91.43 1/s times Ts = 50 us */
#define PERIOD_F        ((float)PWM_PERIOD_COUNTS)
#define DUTY_MAX        ((float)PWM_MAX_COUNTS / PERIOD_F)
#define VREF_RAMP_V     0.0025f    /* per sample: 0.05 V/ms */
#define VOUT_TRIP_V     8.5f
#define VIN_HIGH_TRIP_V 13.0f      /* VIN_SENSE saturates near 13.2 V */
#define VIN_LOW_TRIP_V  9.0f
#define VIN_START_MIN_V 10.5f
#define TRIP_SAMPLES    60u        /* 3 ms */
#define EMA_ALPHA       (1.0f / 256.0f)
#define ADC_FULL_SCALE  4095.0f
#define DIVIDER_INV     4.0f       /* 30k/10k dividers */
#define CAL_MIN         0.95f
#define CAL_MAX         1.05f

/* Loop state: written by the ISR, or by main with interrupts locked. */
static volatile bool closed;
static volatile bool start_req;
static volatile float vref_target = 6.0f;
static volatile float vref_now;
static float integ;

/* Measurements. */
static uint32_t vdda;
static volatile float vout_cal = 1.0f;
static volatile float vout_scale;
static float vin_scale;
static volatile float vout_ema;
static volatile float vin_ema;
static bool ema_ready;
static volatile uint32_t sample_count;

/* Protections. */
static volatile bool vin_low_guard = true;
static volatile trip_t trip;
static uint32_t n_vout_high;
static uint32_t n_vin_high;
static uint32_t n_vin_low;

/* Capture: the ISR fills ring[]; main copies a finished capture into snap[]. */
static capture_sample_t ring[CAPTURE_LEN];
static capture_sample_t snap[CAPTURE_LEN];
static volatile uint32_t ring_head;
static volatile uint32_t ring_fill;
static volatile uint32_t post_left;
static volatile uint32_t trig_index;
static volatile uint32_t trig_pre;
static volatile bool event_req;
static volatile bool ring_frozen;
static uint32_t snap_count;
static uint32_t snap_pre;

static float clampf(float x, float lo, float hi) { return (x < lo) ? lo : ((x > hi) ? hi : x); }

static uint16_t to_u16_milli(float v)
{
    const float mv = v * 1000.0f + 0.5f;
    return (mv <= 0.0f) ? 0u : ((mv >= 65535.0f) ? 65535u : (uint16_t)mv);
}

void control_init(uint32_t vdda_mv)
{
    vdda = vdda_mv;
    vin_scale = (float)vdda_mv * 0.001f * DIVIDER_INV / ADC_FULL_SCALE;
    vout_scale = vin_scale * vout_cal;
}

static uint32_t count_if(bool cond, uint32_t n) { return cond ? n + 1u : 0u; }

/* Returns the trip reason once a limit has held for TRIP_SAMPLES samples. */
static trip_t detect_trip(float vout, float vin, bool active)
{
    if (!active) {
        n_vout_high = n_vin_high = n_vin_low = 0u;
        return TRIP_NONE;
    }
    n_vout_high = count_if(vout > VOUT_TRIP_V, n_vout_high);
    n_vin_high = count_if(vin > VIN_HIGH_TRIP_V, n_vin_high);
    n_vin_low = count_if(vin_low_guard && vin < VIN_LOW_TRIP_V, n_vin_low);
    if (n_vout_high >= TRIP_SAMPLES) {
        return TRIP_VOUT_HIGH;
    }
    if (n_vin_high >= TRIP_SAMPLES) {
        return TRIP_VIN_HIGH;
    }
    return (n_vin_low >= TRIP_SAMPLES) ? TRIP_VIN_LOW : TRIP_NONE;
}

static uint32_t pi_update(float vout)
{
    const float target = vref_target;
    float ref = vref_now;
    if (ref < target) {
        ref = (target - ref > VREF_RAMP_V) ? ref + VREF_RAMP_V : target;
    } else if (ref > target) {
        ref = (ref - target > VREF_RAMP_V) ? ref - VREF_RAMP_V : target;
    }
    vref_now = ref;

    const float e = ref - vout;
    float i_new = integ + KI_TS * e;
    float u = KP * e + i_new;
    if ((u > DUTY_MAX && e > 0.0f) || (u < 0.0f && e < 0.0f)) {
        i_new = integ; /* conditional integration (anti-windup) */
        u = KP * e + integ;
    }
    integ = clampf(i_new, 0.0f, DUTY_MAX);
    u = clampf(u, 0.0f, DUTY_MAX);
    return (uint32_t)(u * PERIOD_F + 0.5f);
}

static void capture_record(float vout, uint32_t ccr)
{
    if (ring_frozen) {
        event_req = false; /* drop it: a late trigger would mislabel the capture */
        return;
    }
    const uint32_t head = ring_head;
    ring[head].vref_mv = closed ? to_u16_milli(vref_now) : 0u;
    ring[head].vout_mv = to_u16_milli(vout);
    ring[head].ccr = (uint16_t)ccr;
    if (event_req) {
        event_req = false;
        if (post_left == 0u) { /* ignore events while a capture is running */
            trig_index = head;
            trig_pre = (ring_fill < CAPTURE_PRE) ? ring_fill : CAPTURE_PRE;
            post_left = CAPTURE_LEN - CAPTURE_PRE;
        }
    }
    ring_head = (head + 1u) % CAPTURE_LEN;
    if (ring_fill < CAPTURE_LEN) {
        ring_fill++;
    }
    if (post_left > 0u && --post_left == 0u) {
        ring_frozen = true;
    }
}

void control_on_sample(uint16_t vout_raw, uint16_t vin_raw)
{
    sample_count++;
    const float vout = (float)vout_raw * vout_scale;
    const float vin = (float)vin_raw * vin_scale;
    if (!ema_ready) {
        vout_ema = vout;
        vin_ema = vin;
        ema_ready = true;
    }
    vout_ema += (vout - vout_ema) * EMA_ALPHA;
    vin_ema += (vin - vin_ema) * EMA_ALPHA;

    uint32_t ccr = hw_pwm_counts();
    const trip_t t = detect_trip(vout, vin, closed || start_req || ccr > 0u);
    if (t != TRIP_NONE) {
        hw_pwm_trip();
        closed = false;
        start_req = false;
        trip = t;
        ccr = 0u;
    } else if (start_req) {
        start_req = false;
        integ = (float)ccr / PERIOD_F; /* bumpless: e = 0 at the first sample */
        vref_now = vout;
        closed = true;
    }
    if (closed) {
        ccr = pi_update(vout);
        hw_pwm_set_counts(ccr);
    }
    capture_record(vout, ccr);
}

bool control_is_closed(void) { return closed; }

bool control_pi_start(float vref_target_v)
{
    if (vin_low_guard && vin_ema < VIN_START_MIN_V) {
        return false;
    }
    const uint32_t key = hw_irq_lock();
    vref_target = vref_target_v;
    if (!closed) {
        start_req = true;
    }
    hw_irq_unlock(key);
    return true;
}

uint32_t control_pi_stop(void)
{
    const uint32_t key = hw_irq_lock();
    closed = false;
    start_req = false;
    const uint32_t ccr = hw_pwm_counts();
    hw_irq_unlock(key);
    return ccr;
}

void control_force_open(void) { (void)control_pi_stop(); }

bool control_vref_step(float vref_v)
{
    const uint32_t key = hw_irq_lock();
    const float delta = vref_v - vref_now;
    const bool ok = closed && delta <= CONTROL_VREF_STEP_MAX_V && delta >= -CONTROL_VREF_STEP_MAX_V;
    if (ok) {
        vref_target = vref_v;
        vref_now = vref_v;
        event_req = true;
    }
    hw_irq_unlock(key);
    return ok;
}

void control_set_vref_target(float vref_v) { vref_target = vref_v; }
float control_vref_target(void) { return vref_target; }
float control_vref_now(void) { return closed ? vref_now : 0.0f; }
uint32_t control_duty_counts(void) { return hw_pwm_counts(); }
uint32_t control_sample_count(void) { return sample_count; }
float control_vout_v(void) { return vout_ema; }
float control_vin_v(void) { return vin_ema; }
uint32_t control_vdda_mv(void) { return vdda; }
float control_vout_cal(void) { return vout_cal; }

bool control_calibrate_vout(float measured_v)
{
    const float reading = vout_ema;
    if (reading < 1.0f || measured_v < 1.0f) {
        return false;
    }
    const float cal = vout_cal * measured_v / reading;
    if (cal < CAL_MIN || cal > CAL_MAX) {
        return false;
    }
    vout_cal = cal;
    vout_scale = vin_scale * cal;
    vout_ema = measured_v;
    return true;
}

void control_set_vin_low_guard(bool on) { vin_low_guard = on; }
bool control_vin_low_guard(void) { return vin_low_guard; }

trip_t control_take_trip(void)
{
    const uint32_t key = hw_irq_lock();
    const trip_t t = trip;
    trip = TRIP_NONE;
    hw_irq_unlock(key);
    return t;
}

void control_mark_event(void) { event_req = true; }

bool control_capture_poll(void)
{
    if (!ring_frozen) {
        return false;
    }
    /* ISR is not writing while frozen: linearise pre + post samples. */
    const uint32_t pre = trig_pre;
    const uint32_t count = pre + (CAPTURE_LEN - CAPTURE_PRE);
    const uint32_t start = (trig_index + CAPTURE_LEN - pre) % CAPTURE_LEN;
    for (uint32_t i = 0u; i < count; i++) {
        snap[i] = ring[(start + i) % CAPTURE_LEN];
    }
    snap_count = count;
    snap_pre = pre;
    ring_fill = 0u; /* pre-event data must be newer than this capture */
    ring_frozen = false;
    return true;
}

uint32_t control_capture_count(void) { return snap_count; }
uint32_t control_capture_pre(void) { return snap_pre; }
capture_sample_t control_capture_sample(uint32_t i) { return snap[(i < snap_count) ? i : 0u]; }
