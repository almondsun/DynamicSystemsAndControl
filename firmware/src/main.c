/* main.c - Buck Rev C firmware (NUCLEO-L432KC): open-loop bring-up and the
 * Entrega 4 closed-loop PI, driven from a serial console (115200 8N1, 'h').
 *
 * Safety: PWM off, loads off and PI off at boot; open-loop duty ramped
 * (1 %/20 ms) and clamped to 0.85; unramped steps <= 0.15; PI starts bumpless
 * with a 0.05 V/ms reference ramp and only with VIN present; the ADC interrupt
 * trips the PWM if VOUT > 8.5 V, VIN > 13 V or VIN < 9 V for 3 ms; 0.5 s
 * watchdog. Any reset leaves Q1 off by hardware (R2).
 */
#include <ctype.h>
#include <math.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "control.h"
#include "hw.h"

#define FW_VERSION         "2.0"
#define RAMP_COUNTS_PER_MS 2u   /* 2/4000 per ms = 1 % per 20 ms */
#define STEP_MAX_COUNTS    600u /* 0.15 */
#define LOG_MIN_PERIOD_MS  10u
#define LOG_MAX_PERIOD_MS  60000u
#define LINE_MAX           48u
#define OUT_MAX            192u
#define TS_US              50   /* nominal PWM period for the dump time axis */

_Static_assert(PWM_MAX_COUNTS <= PWM_PERIOD_COUNTS, "duty clamp above period");

static uint32_t duty_now;    /* open loop: counts written to the timer */
static uint32_t duty_target; /* open loop: ramp target, counts */
static uint32_t log_period_ms;
static uint32_t log_last_ms;
static uint32_t dump_next;   /* next capture row to print */
static bool dumping;

/* ---------- output helpers ---------- */

static void out(const char *fmt, ...)
{
    char buf[OUT_MAX];
    va_list ap;
    va_start(ap, fmt);
    const int n = vsnprintf(buf, sizeof buf, fmt, ap);
    va_end(ap);
    if (n > 0) {
        hw_uart_write(buf, ((size_t)n < sizeof buf) ? (size_t)n : sizeof buf - 1u);
    }
}

/* counts -> "0.xxxx" */
static const char *duty_str(uint32_t counts, char *buf, size_t len)
{
    const uint32_t d4 = (counts * 10000u + PWM_PERIOD_COUNTS / 2u) / PWM_PERIOD_COUNTS;
    snprintf(buf, len, "%lu.%04lu", (unsigned long)(d4 / 10000u), (unsigned long)(d4 % 10000u));
    return buf;
}

static uint32_t to_mv(float v) { return (v <= 0.0f) ? 0u : (uint32_t)(v * 1000.0f + 0.5f); }

/* mV -> "x.xxx" */
static const char *mv_str(uint32_t mv, char *buf, size_t len)
{
    snprintf(buf, len, "%lu.%03lu", (unsigned long)(mv / 1000u), (unsigned long)(mv % 1000u));
    return buf;
}

static void prompt(void) { out("> "); }

/* ---------- argument parsing ---------- */

static bool parse_float(const char *s, float lo, float hi, float *v)
{
    if (s == NULL) {
        return false;
    }
    char *end = NULL;
    const float x = strtof(s, &end);
    if (end == s || *end != '\0' || !isfinite(x) || x < lo || x > hi) {
        return false;
    }
    *v = x;
    return true;
}

static bool parse_duty(const char *s, uint32_t *counts)
{
    float d;
    if (!parse_float(s, 0.0f, 0.86f, &d)) { /* range check before converting */
        return false;
    }
    const uint32_t c = (uint32_t)(d * (float)PWM_PERIOD_COUNTS + 0.5f);
    if (c > PWM_MAX_COUNTS) {
        return false;
    }
    *counts = c;
    return true;
}

static bool parse_bit(const char *s, bool *on)
{
    if (s != NULL && (strcmp(s, "0") == 0 || strcmp(s, "1") == 0)) {
        *on = (s[0] == '1');
        return true;
    }
    return false;
}

/* ---------- state changes ---------- */

static void pwm_stop_now(void)
{
    control_force_open();
    hw_pwm_off();
    duty_now = 0u;
    duty_target = 0u;
}

static void mark_event(void)
{
    hw_trig_set(!hw_trig_get());
    control_mark_event();
}

static bool require_open(void)
{
    if (control_is_closed()) {
        out("ERROR: PI activo, usa 'pi off' primero\r\n");
        return false;
    }
    return true;
}

/* ---------- commands ---------- */

static void cmd_help(const char *arg)
{
    (void)arg;
    static const char help[] =
        "Lazo abierto:\r\n"
        "  d <0-0.85>   duty con rampa 1 %/20 ms (ej: d 0.10)\r\n"
        "  step <d>     duty sin rampa, |cambio| <= 0.15, evento\r\n"
        "Lazo cerrado (PI Entrega 3):\r\n"
        "  pi on        arranca el PI sin salto; vref sube en rampa al objetivo\r\n"
        "  pi off       sale del PI y mantiene el duty actual en lazo abierto\r\n"
        "  v <3-7.5>    con PI: escalon de referencia (<= 1.5 V), evento\r\n"
        "               sin PI: objetivo para el proximo 'pi on' (inicial 6.0)\r\n"
        "Ambos:\r\n"
        "  x            APAGADO inmediato (PWM y PI)\r\n"
        "  a <0|1>      carga 36R (LSW_A), evento\r\n"
        "  b <0|1>      carga 24R (LSW_B), evento\r\n"
        "  t <0|1>      TRIG manual\r\n"
        "  s            estado\r\n"
        "  log <ms>     CSV t_ms,vref_mV,d,vin_mV,vout_mV (10-60000, 0 = off)\r\n"
        "  dump         CSV de la ultima captura (100 ms por periodo PWM, 10 ms antes)\r\n"
        "  cal <V>      calibra VOUT con la lectura del multimetro\r\n"
        "  vmin <0|1>   proteccion VIN baja (1 = activa)\r\n"
        "Evento = invierte TRIG y dispara una captura.\r\n";
    hw_uart_write(help, sizeof help - 1u); /* longer than the out() buffer */
}

static void cmd_status(const char *arg)
{
    (void)arg;
    char a[12];
    char b[12];
    char c[12];
    char e[12];
    out("Modo %s  vref %s V (actual %s)  d=%s  objetivo LA %s\r\n", control_is_closed() ? "PI" : "LAZO ABIERTO",
        mv_str(to_mv(control_vref_target()), a, sizeof a), mv_str(to_mv(control_vref_now()), b, sizeof b),
        duty_str(control_duty_counts(), c, sizeof c), duty_str(duty_target, e, sizeof e));
    out("VIN=%s V  ", mv_str(to_mv(control_vin_v()), a, sizeof a));
    out("VOUT=%s V  VDDA=%lu mV  cal=%lu ppm  A=%d B=%d TRIG=%d vmin=%d\r\n",
        mv_str(to_mv(control_vout_v()), b, sizeof b), (unsigned long)control_vdda_mv(),
        (unsigned long)(control_vout_cal() * 1e6f + 0.5f), hw_load_get(LOAD_SW_A), hw_load_get(LOAD_SW_B),
        hw_trig_get(), control_vin_low_guard());
    out("muestras=%lu  t=%lu ms\r\n", (unsigned long)control_sample_count(), (unsigned long)hw_millis());
}

static void cmd_duty(const char *arg)
{
    uint32_t c;
    if (!require_open()) {
        return;
    }
    if (!parse_duty(arg, &c)) {
        out("ERROR: d 0..0.85\r\n");
        return;
    }
    duty_target = c;
    out("OK\r\n");
}

static void cmd_step(const char *arg)
{
    uint32_t c;
    if (!require_open()) {
        return;
    }
    if (!parse_duty(arg, &c)) {
        out("ERROR: step 0..0.85\r\n");
        return;
    }
    if (duty_now != duty_target) {
        out("ERROR: espera a que termine la rampa\r\n");
        return;
    }
    const uint32_t delta = (c > duty_now) ? c - duty_now : duty_now - c;
    if (delta > STEP_MAX_COUNTS) {
        out("ERROR: escalon mayor a 0.15, usa 'd'\r\n");
        return;
    }
    duty_now = c;
    duty_target = c;
    hw_pwm_set_counts(c);
    mark_event();
    out("OK\r\n");
}

static void cmd_pi(const char *arg)
{
    if (arg != NULL && strcmp(arg, "on") == 0) {
        if (control_is_closed()) {
            out("PI ya activo\r\n");
        } else if (control_pi_start(control_vref_target())) {
            duty_target = duty_now; /* stop any open-loop ramp */
            mark_event(); /* captures the soft start */
            out("OK: PI activo, vref en rampa hacia el objetivo\r\n");
        } else {
            out("ERROR: VIN < 10.5 V, enciende la fuente (o 'vmin 0' para probar sin potencia)\r\n");
        }
    } else if (arg != NULL && strcmp(arg, "off") == 0) {
        duty_now = control_pi_stop();
        duty_target = duty_now;
        out("OK: lazo abierto, duty mantenido. 'd 0.10' o 'x' para bajar\r\n");
    } else {
        out("ERROR: pi on | pi off\r\n");
    }
}

static void cmd_vref(const char *arg)
{
    float v;
    if (!parse_float(arg, CONTROL_VREF_MIN_V, CONTROL_VREF_MAX_V, &v)) {
        out("ERROR: v 3.0..7.5\r\n");
        return;
    }
    if (!control_is_closed()) {
        control_set_vref_target(v);
        out("OK: objetivo para 'pi on'\r\n");
        return;
    }
    hw_trig_set(!hw_trig_get()); /* same instant as the reference step */
    if (control_vref_step(v)) {
        out("OK\r\n");
    } else {
        hw_trig_set(!hw_trig_get());
        out("ERROR: escalon mayor a 1.5 V o rampa en curso\r\n");
    }
}

static void cmd_x(const char *arg)
{
    (void)arg;
    pwm_stop_now();
    out("PWM OFF, PI OFF\r\n");
}

static void cmd_load(load_sw_t sw, const char *arg)
{
    bool on;
    if (!parse_bit(arg, &on)) {
        out("ERROR: usa 0 o 1\r\n");
        return;
    }
    hw_load_set(sw, on);
    mark_event();
    out("OK\r\n");
}

static void cmd_load_a(const char *arg) { cmd_load(LOAD_SW_A, arg); }
static void cmd_load_b(const char *arg) { cmd_load(LOAD_SW_B, arg); }

static void cmd_trig(const char *arg)
{
    bool on;
    if (!parse_bit(arg, &on)) {
        out("ERROR: t 0|1\r\n");
        return;
    }
    hw_trig_set(on);
    out("OK\r\n");
}

static void cmd_log(const char *arg)
{
    char *end = NULL;
    const unsigned long ms = (arg != NULL) ? strtoul(arg, &end, 10) : 0ul;
    if (arg == NULL || end == arg || *end != '\0' ||
        (ms != 0ul && (ms < LOG_MIN_PERIOD_MS || ms > LOG_MAX_PERIOD_MS))) {
        out("ERROR: log 0 o 10..60000\r\n");
        return;
    }
    log_period_ms = (uint32_t)ms;
    log_last_ms = hw_millis();
    if (ms != 0ul) {
        out("t_ms,vref_mV,d,vin_mV,vout_mV\r\n");
    }
}

static void cmd_dump(const char *arg)
{
    (void)arg;
    if (control_capture_count() == 0u) {
        out("ERROR: no hay captura (provoca un evento: v, a, b o step)\r\n");
        return;
    }
    out("# evento en n=%lu, Ts=%d us\r\nn,t_us,vref_V,vout_V,d\r\n", (unsigned long)control_capture_pre(), TS_US);
    dump_next = 0u;
    dumping = true;
}

static void cmd_cal(const char *arg)
{
    float v;
    if (!require_open()) { /* a gain change would bump the closed loop */
        return;
    }
    if (!parse_float(arg, 1.0f, 9.0f, &v) || !control_calibrate_vout(v)) {
        out("ERROR: cal <V del multimetro>, VOUT > 1 V y correccion <= 5 %%\r\n");
        return;
    }
    out("OK: cal = %lu ppm\r\n", (unsigned long)(control_vout_cal() * 1e6f + 0.5f));
}

static void cmd_vmin(const char *arg)
{
    bool on;
    if (!parse_bit(arg, &on)) {
        out("ERROR: vmin 0|1\r\n");
        return;
    }
    control_set_vin_low_guard(on);
    out(on ? "OK: proteccion VIN baja activa\r\n" : "OK: proteccion VIN baja DESACTIVADA (solo sin potencia)\r\n");
}

typedef struct {
    const char *name;
    void (*fn)(const char *arg);
} command_t;

static const command_t COMMANDS[] = {
    {"h", cmd_help},     {"?", cmd_help},   {"s", cmd_status}, {"d", cmd_duty},    {"step", cmd_step},
    {"pi", cmd_pi},      {"v", cmd_vref},   {"x", cmd_x},      {"a", cmd_load_a},  {"b", cmd_load_b},
    {"t", cmd_trig},     {"log", cmd_log},  {"dump", cmd_dump}, {"cal", cmd_cal},  {"vmin", cmd_vmin},
};

static void execute(char *line)
{
    for (char *p = line; *p != '\0'; p++) {
        *p = (char)tolower((unsigned char)*p);
    }
    const char *cmd = strtok(line, " \t");
    const char *arg = strtok(NULL, " \t");
    if (cmd == NULL) {
        return;
    }
    for (size_t i = 0u; i < sizeof COMMANDS / sizeof COMMANDS[0]; i++) {
        if (strcmp(cmd, COMMANDS[i].name) == 0) {
            COMMANDS[i].fn(arg);
            return;
        }
    }
    out("? comando desconocido, 'h' = ayuda\r\n");
}

/* ---------- main loop tasks ---------- */

static void console_poll(void)
{
    static char line[LINE_MAX];
    static size_t len;
    int c;
    while ((c = hw_uart_getc()) >= 0) {
        if (c == '\r' || c == '\n') {
            if (len > 0u) {
                out("\r\n");
                line[len] = '\0';
                len = 0u;
                execute(line);
                if (!dumping) { /* dump_tick prints the prompt after "# fin" */
                    prompt();
                }
            }
        } else if (c == 0x08 || c == 0x7F) {
            if (len > 0u) {
                len--;
                out("\b \b");
            }
        } else if (c >= 0x20 && c <= 0x7E && len < LINE_MAX - 1u) {
            line[len++] = (char)c;
            const char ch = (char)c;
            hw_uart_write(&ch, 1u);
        }
    }
}

static void handle_trip(void)
{
    static const char *const REASON[] = {"", "VOUT > 8.5 V", "VIN > 13 V", "VIN < 9 V"};
    const trip_t t = control_take_trip();
    if (t == TRIP_NONE) {
        return;
    }
    duty_now = 0u;
    duty_target = 0u;
    hw_pwm_release(); /* duty is 0 now, the ramp starts from there */
    out("\r\n*** DISPARO (%s): PWM OFF, PI OFF ***\r\n", REASON[t]);
    prompt();
}

/* 1 ms: open-loop duty ramp (the PI writes the duty itself when closed). */
static void open_loop_tick(void)
{
    if (control_is_closed()) {
        return;
    }
    if (duty_now < duty_target) {
        const uint32_t up = duty_now + RAMP_COUNTS_PER_MS;
        duty_now = (up > duty_target) ? duty_target : up;
    } else if (duty_now > duty_target) {
        duty_now = (duty_now - duty_target > RAMP_COUNTS_PER_MS) ? duty_now - RAMP_COUNTS_PER_MS : duty_target;
    }
    hw_pwm_set_counts(duty_now);
}

static void log_tick(uint32_t now)
{
    if (dumping || log_period_ms == 0u || (now - log_last_ms) < log_period_ms) {
        return;
    }
    log_last_ms = now;
    char d[12];
    out("%lu,%lu,%s,%lu,%lu\r\n", (unsigned long)now, (unsigned long)to_mv(control_vref_now()),
        duty_str(control_duty_counts(), d, sizeof d), (unsigned long)to_mv(control_vin_v()),
        (unsigned long)to_mv(control_vout_v()));
}

/* One capture row per main-loop pass, so the loop and watchdog keep running. */
static void dump_tick(void)
{
    if (!dumping) {
        return;
    }
    if (dump_next >= control_capture_count()) {
        dumping = false;
        out("# fin\r\n");
        prompt();
        return;
    }
    const capture_sample_t s = control_capture_sample(dump_next);
    const long t_us = ((long)dump_next - (long)control_capture_pre()) * TS_US;
    char a[12];
    char b[12];
    char c[12];
    out("%lu,%ld,%s,%s,%s\r\n", (unsigned long)dump_next, t_us, mv_str(s.vref_mv, a, sizeof a),
        mv_str(s.vout_mv, b, sizeof b), duty_str(s.ccr, c, sizeof c));
    dump_next++;
}

int main(void)
{
    hw_init();
    control_init(hw_vdda_mv());
    hw_start_sampling(control_on_sample);

    out("\r\n\r\nBuck Rev C fw %s | SYSCLK %lu MHz | PWM %lu Hz | d max 0.85 | PI Kp 0.030477 KiTs 0.0045716\r\n",
        FW_VERSION, (unsigned long)(hw_sysclk_hz() / 1000000u),
        (unsigned long)(hw_sysclk_hz() / PWM_PERIOD_COUNTS));
    if (hw_reset_was_watchdog()) {
        out("AVISO: reinicio por watchdog\r\n");
    }
    out("PWM OFF, PI OFF, cargas OFF, TRIG 0. 'h' = ayuda\r\n");
    prompt();

    uint32_t last_ms = hw_millis();
    for (;;) {
        hw_wdg_kick();
        handle_trip();
        console_poll();
        if (!dumping && control_capture_poll()) { /* keep snap[] stable during a dump */
            out("\r\n[captura lista: %lu muestras, 'dump']\r\n", (unsigned long)control_capture_count());
            prompt();
        }
        dump_tick();
        const uint32_t now = hw_millis();
        if (now != last_ms) {
            last_ms = now;
            open_loop_tick();
            log_tick(now);
        }
    }
}
