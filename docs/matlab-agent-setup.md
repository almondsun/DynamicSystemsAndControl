# MATLAB agent setup

## Start a shared session

Open MATLAB with `matlab` in Fish. In MATLAB's Command Window run:

```matlab
addpath('/home/mitin/.matlab/agentic-toolkits/simulink')
satk_initialize
```

This initializes the official Simulink toolkit and explicitly shares this session.
It must be repeated after restarting MATLAB. No `startup.m` was modified. If you
share multiple sessions, the MCP server attaches to the most recently shared one.

Start a fresh Codex session after installation to load its new tools and skills.
Use `/mcp` to check the MATLAB connection. Ask Codex to report the MATLAB version,
inspect an open model, or run a script. An existing-session connection requires
MATLAB to remain running; it will not silently create a replacement session.

## Installed integration

Official upstreams and pinned versions:

- https://github.com/matlab/matlab-mcp-server — v0.13.0
- https://github.com/matlab/matlab-agentic-toolkit — 2026.08.27,
  commit `922e92e7903eded70bedbffe3f68bcf5690ddcdc`
- https://github.com/matlab/simulink-agentic-toolkit — SATK-2026.09.a,
  commit `831e8491ebd7d02adec516c097d552e3ac5cc9ec`

Artifacts were installed by the official installer from verified local downloads
under `~/.matlab/agentic-toolkits/downloads/`. Repository copies appear as `local`
in installer status; the commits above identify their actual versions.

The user-wide Codex MCP configuration uses local STDIO, existing-session mode,
the Simulink extension, disabled telemetry, and a 600-second tool timeout.
`model_test` is disabled because Simulink Test is not installed. Core MATLAB
testing remains available. Existing Codex settings and Fish aliases are preserved.

Twenty skills are linked into `~/.agents/skills/`: MATLAB Core, Model-Based
Design Core, Simulink Simulation, and Simulink Environment Fundamentals.
The control-specific skill groups require additional products and were excluded.
Control System Toolbox functions such as `tf` and `step` remain usable via MATLAB.
Skills mentioning optional toolboxes do not establish that those are licensed.

## Reproducible validation

From the project directory, run in MATLAB:

```matlab
addpath('tools')
agentValidation = validate_matlab_agent()
```

Or run the same check from a terminal:

```sh
/home/mitin/MATLAB/R2026a/bin/matlab -batch "addpath('/home/mitin/code/uni/DynamicSystemsAndControl/tools'); validate_matlab_agent();"
```

The helper copies the course script to a unique folder under `artifacts/`, runs
it in function scope, saves the generated model and numerical results, and
exports `speed.png`. Expected: 10 m/s steady speed, 20 s time constant, 9.9752 m/s
at 120 s, and less than 0.001 m/s numerical error. It leaves its generated model
open for inspection without clearing the user's base workspace.

## Maintenance and rollback

The pre-install Codex configuration is backed up at
`~/.matlab/agentic-toolkits/backups/20260908T104036/codex-config.toml`.
To disconnect only this integration, use `codex mcp remove matlab`, then restart
Codex. Do not restore the entire old config over later unrelated changes.
The official installer supports `setupAgenticToolkit("uninstall")`; inspect its
proposed removal scope before confirming. Remove only this toolkit's skill links.

Updates are deliberate: inspect release notes, update through the official
installer, recheck existing-session mode/telemetry/tool exclusions, and rerun the
numerical and connection checks. The current directory is not a security sandbox.

## Platform caveat

This machine runs Omarchy/Arch with MATLAB R2026a Update 5. The earlier terminal
output showed a graphics-library incompatibility and a fatal shutdown error.
Initial batch and non-graphical smoke tests exited normally. On September 9,
the actual desktop successfully compiled the model and plotted results, but
closing it through Hyprland reproduced `GLIBCXX_3.4.32 not found`,
`free(): chunks in smallbin corrupted`, and MATLAB fatal exit status 9.
The bundled C++ runtime is `libstdc++.so.6.0.30`; the system runtime is
`libstdc++.so.6.0.36`. Do not apply the installer-only GnuTLS workaround globally
or replace bundled libraries without evidence and testing.

A launch-only experiment with `LD_PRELOAD=/usr/lib/libstdc++.so.6` verified the
system runtime was loaded in both MATLAB and its desktop process. Simulation and
plotting passed, and the GLIBCXX/libva/MESA errors disappeared. Nevertheless,
window-close still ended with heap corruption and exit status 9. The override
was therefore **not persisted**; the `matlab` Fish shortcut is unchanged.

Both MATLAB crash reports show allocator aborts during process-context teardown,
with MATLAB message-service cleanup in the baseline trace and thread-pool/service
tracker cleanup in the override trace. These identify where corruption was
detected, not where it originated. The raw reports remain in the home directory
(`matlab_crash_dump.15924-1` and `matlab_crash_dump.20234-1`); they contain session
and entitlement identifiers and have not been copied into this project or sent
to MathWorks. No system or MATLAB runtime libraries were changed.

**Status:** Agent connection, modeling, numerical simulation, and desktop
diagnostics are verified. Desktop shutdown remains a reproduced platform issue;
the local installation is provisional. Save work before closing MATLAB.

A final real-desktop test without `satk_initialize` or an MCP connection plotted
successfully and then called MATLAB's normal `exit`. It also failed with heap
corruption and status 9. `artifacts/normal-desktop-exit.log` records the startup
and requested normal exit. Thus the failure is not limited to Super+W or a shared
agent session. Batch startup, plotting, and exit passed earlier; those runs did
not exercise the actual desktop shutdown path.

## Validation record

The September 8 integration probe passed toolbox detection, shared-session marker
verification, Code Analyzer (no issues in the course script), model inspection,
and connectivity checks. The numerical result was 9.975212478232914 m/s at 120 s,
with maximum error 1.0222e-11 m/s. `artifacts/mcp-validation.json` records the
calls; the generated plot and MAT data are in the adjacent unique output folder.

The disposable model edit test doubled driving force from 500 N to 1000 N and
verified the corresponding doubled speed, then restored 500 N and saved the copy.
`artifacts/mcp-edit.json` records these checks. The toolkit's Step parameter is
`FinalValue`, not the lower-level `After` alias used by the generator. Always
check model tool status text; a transport-level success can contain `status: error`.

The initial diagnostics-reader attempt did not finish in the session without a
desktop. That call is not counted as passing. On September 9, a fresh Codex session
discovered the configured tools and 20 skills. With MATLAB closed, it returned
`failed to attach to MATLAB session`; after starting and explicitly sharing a
session on the real desktop, the same Codex connection successfully verified its
marker, MATLAB version, `usejava('desktop') == 1`, and `DISPLAY=:0`.
The actual desktop also passed model compilation, plotting, and
`model_read_diagnostics` (zero errors, warnings, or informational messages).
