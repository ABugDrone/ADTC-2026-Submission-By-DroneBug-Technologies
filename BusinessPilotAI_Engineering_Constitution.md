# BusinessPilot AI - Engineering Constitution

## Core Principles

1. Never sacrifice maintainability for fewer lines of code.
2. Every module must have a single responsibility.
3. Never duplicate business logic.
4. Every public function must be documented.
5. Every feature must include corresponding tests.
6. Prefer composition over inheritance.
7. Prefer explicit code over hidden abstractions.
8. Keep dependencies to the minimum required.
9. Optimize CPU and RAM usage before adding features.
10. Never add a dependency if the standard library can solve the problem cleanly.
11. Every commit must leave the project in a runnable state.
12. Every optimization must be measurable with benchmarks.
13. Build the smallest working implementation first, then iterate.
14. Keep agent execution deterministic wherever practical.
15. Logging, error handling and documentation are mandatory for every feature.

## AI-Specific Rules

- No cloud inference.
- Open-source components only.
- Offline-first architecture.
- Reflection only when justified.
- Never reload the model unnecessarily.
- Reuse resources wherever possible.
- Keep prompts modular and version-controlled.

## Code Quality

- Python: PEP8, type hints, docstrings.
- React: Functional components with strict TypeScript.
- Rust: Idiomatic and safe.
- Consistent formatting and linting.
- Prefer readable code over clever code.

## Performance Targets

- Fast startup.
- Stable memory usage.
- Responsive UI during inference.
- Graceful degradation on low-end hardware.
- Measure before optimizing.

## Release Criteria

A feature is complete only when it:
- Works correctly.
- Includes tests.
- Is documented.
- Handles errors gracefully.
- Meets performance expectations.
