## Description: <br>
PPT Generator turns a user speech draft into a Steve Jobs-style minimalist, technology-focused 9:16 HTML presentation delivered as a single runnable HTML file. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[wwlyzzyorg](https://clawhub.ai/user/wwlyzzyorg) <br>

### License/Terms of Use: <br>


## Use Case: <br>
External users and creators use this skill to condense a speech draft, plan a slide structure, and generate a minimalist vertical HTML presentation for talks, demos, or social sharing. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Generated presentations rely on CDN-hosted TailwindCSS and fonts, which may not fit confidential, offline, or tightly controlled presentation environments. <br>
Mitigation: Review or replace CDN links before using the output in controlled environments. <br>
Risk: The skill is Chinese-oriented by default and may produce Chinese presentation text when another language is expected. <br>
Mitigation: Explicitly request the desired output language and review the generated manuscript before presenting. <br>
Risk: Condensing a speech draft can omit details or shift emphasis from the original material. <br>
Mitigation: Review the refined manuscript and slide outline against the source draft before using the generated deck. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/wwlyzzyorg/skills/ppt-generator) <br>
- [Design specification](references/design-spec.md) <br>
- [Slide types](references/slide-types.md) <br>


## Skill Output: <br>
**Output Type(s):** [Markdown, Code, Files, Guidance] <br>
**Output Format:** [Markdown response containing a refined manuscript, slide outline, and complete standalone HTML code.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Generates a 9:16 vertical presentation with keyboard navigation, touch navigation, progress indicators, smooth transitions, animated light spots, and CDN dependencies.] <br>

## Skill Version(s): <br>
1.0.0 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
