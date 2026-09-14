# MATLAB and Simulink coursework

- Read the assignment in `classroom/` before choosing equations or parameters.
- Use installed MathWorks agent skills and the MATLAB MCP server. See
  `docs/matlab-agent-setup.md` for session sharing and CLI fallback.
- Read model structure before editing; use the toolkit's model editing and
  connectivity tools for interactive changes. Preserve user models and workspaces.
- Inspect returned status text as well as MCP error flags: model tools can return
  `status: error` inside a successful transport response. Query toolkit parameter
  names before editing (for example, a Step block uses `FinalValue`).
- Do not clear the base workspace, reset the MATLAB path, close unrelated models,
  or quit a user session without task authorization.
- State units, initial conditions, solver settings, and expected responses.
- For validation, use isolated output folders under `artifacts/`; never overwrite
  coursework or manually edit generated `.slx` internals.
- Installed course products: MATLAB, Simulink, Control System Toolbox. Simulink
  Test and Simulink Control Design are not installed. Use numerical assertions
  and MATLAB tests rather than assuming those optional products are available.
- Cruise-control acceptance: `tools/validate_matlab_agent.m`. Run with `tools/`
  on the MATLAB path; it returns output paths and quantitative validation results.
- Report actual runtime results separately from static checks. Keep graphics
  warnings and shutdown failures visible; do not suppress stderr to hide them.
