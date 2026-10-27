# Sistemas Dinámicos y Control

Coursework and final Buck-converter project at Universidad Nacional de Colombia, Sede Manizales.

## Final project

- [Project documentation](project/README.md)
- [Four IEEE deliverable reports](project/reports/final/)
- [Hardware appendix: 3D views, schematics and wiring](project/pcb/release/hardware-appendix.pdf)
- [PCB design and build instructions](project/pcb/README.md)
- [STM32 firmware](project/firmware/README.md)
- [Requirements audit and next steps](project/pcb/docs/requirements-audit.md)
- [Buck SMD/JLCPCB audit: inventory, passive requirements and open issues](project/pcb/audit/README.md)
- [Team review package](project/pcb/release/buck-team-review.zip)

The design targets 12 V input, 6 V nominal output and 10 kHz PWM. Reports distinguish numerical simulations and CAD checks from experimental evidence. Component qualification, prototype assembly and physical testing remain pending; PCB fabrication is on hold.

## Repository contents

- `classroom/`: assignment and course reference material.
- `simulations/`: MATLAB and Simulink coursework.
- `project/`: final-project sources, reports, compact numerical results, PCB and firmware.
- `tools/` and `docs/`: validation helpers and MATLAB setup documentation.

Local downloaded toolchains, full raw validation runs and caches under `artifacts/` are excluded from Git. Follow the project documentation for build dependencies and reproducibility limits. Course materials and third-party assets retain their respective rights; KiCad model licensing is included in `project/pcb/models/`.
