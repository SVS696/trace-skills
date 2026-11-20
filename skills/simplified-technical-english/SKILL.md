---
name: simplified-technical-english
description: Rewrite or check English technical text using an adapted ASD-STE100 and IBM EasyEnglish profile. Use for English requirements, procedures, API documentation, and skill instructions. Also use when a user requests a technical adaptation into English from another language.
---

# Simplified Technical English

Use the supplied source and the project glossary. If the source is in another language and the user requests English, translate the meaning and preserve the strength of each requirement. If only an English draft is available, check that draft for clarity. A check for changes in meaning also requires the source.

## Select the output

- **Rewrite.** Return the revised English text in the requested format. Keep the document structure. List any open decision that affects the result.
- **Check.** Keep the input file unchanged. For each issue, give its location, a short excerpt, the ambiguity or change in meaning, and a proposed correction. If the source cannot support a correction, state the question for the decision owner.
- **Rewrite and check.** Return the revised text first. Then report unresolved issues from the comparison. If the user requests a file edit, apply it to the specified file.

## Edit and verify

1. Identify the text type. In a procedure, put the condition before the action. Give one instruction per step when the actions can be separated. Keep the sequence and any stop condition. In descriptive text, name the component and use the active voice when the source identifies the actor.
2. In a requirement, keep the trigger or state, responsible actor, required response, and exception. Preserve the distinction between permission, obligation, prohibition, and a statement of fact. Use the project's modal verbs. For an event or state, use an EARS pattern if it clarifies the rule.
3. Choose one term for each concept. Use the project's technical nouns and verbs. Check pronouns and long noun groups for a second possible interpretation. Replace an ambiguous expression only if its meaning is known.
4. Keep the stated reason for a rule with the case to which it applies. After a reader edit, use check mode on the changed text. Compare each revised condition with the source. Check inclusive bounds, negation, time limits, units, and atomic operations. Preserve code, UI labels, API names, status values, quotations, and references. For a protocol that adopts BCP 14, retain its normative keywords and their defined meanings. [TRACE writing profile and extensions](../../rules/technical-writing.md)

**Example.** Source: “An operator may retry after 30 s unless the device is OFFLINE.” Rewrite: “If the device is not OFFLINE, the operator may retry after 30 s.” The operator still has permission to retry. The source does not say which event starts the timer. If that detail matters, ask for it.

Use the ASD-STE100 writing approach and the IBM EasyEnglish approach to ambiguity. If the user requests a formal STE compliance assessment, identify the applicable issue and check its rules and approved vocabulary against the text. State the scope of the check and any unavailable material. [ASD-STE100](https://www.asd-ste100.org/about_STE.html) · [IBM EasyEnglish](https://research.ibm.com/publications/easyenglish-a-tool-for-improving-document-quality)
