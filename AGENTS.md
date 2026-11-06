
Inspect the project root and create an `AGENTS.md` file if one does not exist. If it already exists, read it carefully and update it without unnecessarily deleting or overwriting useful existing instructions.

The purpose of this file is to establish strict working rules that you must follow throughout this project.

## AGENT WORKING RULES

### 1. Inspect Before Implementing
- Before making any changes, inspect the existing project structure, relevant files, dependencies, configurations, and current implementation.
- Understand how the existing code works before modifying it.
- Check for existing components, functions, utilities, or solutions before creating new ones.
- Never assume something is missing without inspecting first.
- Identify potential conflicts or side effects before changing existing code.

### 2. Explain Before Building
- Before implementing any requested task, provide the user with a short, clear summary of:
  - What you understood from the request.
  - What you intend to build or change.
  - Which files or areas you expect to modify.
  - How you plan to test the result.
- Wait for the user's approval before starting implementation if the request is ambiguous, involves significant architectural decisions, or could substantially change existing functionality.
- For clear, explicitly authorized tasks, proceed after providing the summary without unnecessary delays.

### 3. Follow the Exact Scope
- Build only what the user explicitly requested.
- Do not introduce additional features, functionality, components, dependencies, redesigns, or architectural changes without permission.
- Do not make unrelated improvements simply because you notice opportunities to improve the project.
- Preserve existing functionality, design decisions, coding conventions, and project architecture unless the requested task requires changing them.
- If you identify an important improvement outside the requested scope, explain it and ask before implementing it.

### 4. Maintain Code Quality
- Write clean, readable, maintainable, and properly structured code.
- Follow the project's existing technology stack and conventions.
- Avoid unnecessary dependencies and duplicated code.
- Use appropriate TypeScript types and avoid `any` unless genuinely necessary.
- Handle errors and edge cases appropriately.
- Never leave placeholder implementations, unfinished functionality, or misleading success states.

### 5. Test Before Handover
- After implementing a task, run the relevant tests and validation checks before presenting the work as complete.
- For frontend changes, check the build and relevant lint/type checks.
- For backend changes, test the affected endpoints and relevant application behavior.
- Verify that existing functionality has not been unnecessarily broken.
- Fix errors caused by your changes before handing over the work.
- Never claim that something works if you have not verified it.
- If a test cannot be performed, clearly explain why and identify what remains unverified.

### 6. Final Handover
After completing a task, provide a concise report containing:
- What was implemented.
- Which files were created or modified.
- What tests and validation checks were performed.
- Whether the tests passed or failed.
- Any remaining limitations or issues.

Do not overwhelm the user with unnecessary technical details.

## MOST IMPORTANT PRINCIPLE

Inspect first. Explain the intended work. Build only what was requested. Test everything relevant. Then hand over the verified result.

These instructions apply to every task in this project. Treat them as persistent project-wide working rules.
