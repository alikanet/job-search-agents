# Set your voice and style

The agents write documents in your name, so they need to sound like you. The template guides ship with **default choices**. They are starting points, not rules, and some will not suit you. Review every item below before you generate anything.

You will edit two files:

- `cv-cover-letter-agent/knowledge/cv_style_guide.md`
- `cv-cover-letter-agent/knowledge/cover_letter_style_guide.md`

When you have finished reviewing a guide, **delete `(TEMPLATE)` from its first line**. The CV and cover letter script will refuse to run until you do, so you cannot forget.

---

## Option A: let an AI work out your voice

Paste the prompt in [`prompts/voice-and-style-review.md`](../prompts/voice-and-style-review.md) into any AI chat, along with two or three samples of your own writing (emails, LinkedIn posts, past cover letters). It will describe how you write and propose wording for the Tone, Sentence style and Punctuation sections.

## Option B: review the checklist yourself

### 1. Tone and voice

Decide the register you want. Examples:

| Register | Sounds like |
|---|---|
| Direct and confident | "I take complex programmes from scoping to go-live." |
| Warm and collaborative | "I enjoy bringing teams together around a shared goal." |
| Measured and formal | "I have extensive experience delivering large-scale programmes." |

Decide:

- First person ("I led...") or implied first person ("Led...")?
- Contractions ("I've", "I'll") allowed or not?
- Is any hedging acceptable ("I believe", "I think")? The default bans it.
- How much personality or humour, if any?

### 2. Sentence style

- Short and punchy, long and flowing, or a mix?
- Are sentence fragments for emphasis acceptable?
- Should the Professional Summary be more expressive than the bullets?
- Do you talk directly to the reader ("you")?

### 3. Punctuation and spelling

- **Spelling:** British (organisation, programme) or American (organization, program)? State it in the guide.
- **Dashes:** the defaults avoid em dashes and en dashes as a stylistic device, because many readers now see them as a sign of AI-written text. Keep or remove this rule as you prefer.
- **Hyphens and quotation marks:** the defaults use straight quotes and normal hyphens, which is safest for application tracking systems.
- **Numbers:** write "5-person" or "five person"? "£3m" or "£3 million"?

### 4. CV rules to check

- **Title line:** tailored to each job (default) or fixed?
- **Which roles to include:** the default keeps recent roles on every CV and includes older ones only when relevant. Change the number to suit you.
- **Passion project section:** keep it, or delete it if you have nothing to put there.
- **Experience framing:** state honestly how long you have worked in your target specialism, so the agent never overstates it.
- **Qualification line:** a certification printed in the contact line (optional).

### 5. Cover letter structure

The default structure is a starting point and you should reshape it. Review each part:

| Part | Default | Questions to ask yourself |
|---|---|---|
| Opening line | A specific reason for applying | Do you want a more formal or more casual opening? |
| Why this company paragraph | Required, in your personal voice | Do you want it at all? Would it work better folded into the opening? |
| Experience paragraphs | 2 or 3 achievements, each with what / how / result | Do you want 2, 3 or 4? Do you prefer bullets? |
| Closing | Brief and confident | Do you want a call to action, such as asking for a conversation? |
| Length | Exactly one page | Is one page right for the roles you apply to? |
| Gap handling | Never apologise for gaps; reframe with transferable skills | Do you prefer to address a gap openly? |
| Sign-off | Added automatically by the script | Is "Kind regards" right for you? Edit it in `tailor_application.py` if not. |

If you change the structure, change the numbered list under **Structure** in the cover letter guide so the agent follows your version.

### 6. Test it

Generate a CV and cover letter for a real job. Read both aloud. Anything that does not sound like you, change in the guide, not in the output, so the fix applies to every future application.

## Why this matters

Hiring teams read many applications. Generic, over-polished writing is easy to spot. Documents that sound like a real person, with specific numbers and plain language, stand out.
