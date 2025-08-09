Thoroughly review every line of code only within the core code directories of this codebase. Follow all logic paths exhaustively across the entire system. Ignore test files, documentation, and non-core utility scripts unless they are directly tied to core application behavior.
Actively identify and document:
	•	Syntax or runtime errors
	•	Incomplete, stubbed, or placeholder sections (e.g., TODOs, mocks, commented-out future plans)
	•	Hardcoded configuration values or credentials that should be parameterized or externally managed
	•	Redundant, duplicate, or overly complex code that adds unnecessary maintenance burden
	•	Deprecated patterns, anti-patterns, or insecure coding practices
	•	Performance bottlenecks or unoptimized logic
	•	Missing validation, exception handling, or logging where appropriate
Ensure the review is complete, holistic, and leaves no component or execution path unchecked. All findings should reflect a comprehensive production-readiness assessment, not a partial or surface-level evaluation.
Confirm that all code:
	•	Is fully functional and adheres to implementation and domain requirements
	•	Meets security, performance, maintainability, and clarity standards
	•	Is documented where necessary for future developers
	•	Avoids fragile or hacky implementations, ensuring long-term operability
Pay meticulous attention to detail throughout the review. Omit nothing. Report everything found.