# Evaluating a prompt

A rewrite that reads better has not been shown to work. Run it on real inputs, compare it with the
original on the same inputs, and report the result per property.

## Build the evaluation set

Collect 10 to 30 inputs. ASSUMPTION: this range is a working rule for a hand-run comparison. Below 10,
one odd case dominates; above 30, reviewing by hand gets skipped. For a prompt in production, grow the
set from real failures over time.

Sources, in order of preference:

1. Real inputs the prompt has already seen, especially the ones that produced bad output.
2. Real inputs of the kinds expected but not yet seen, from the user or from logs.
3. Written cases for situations that are rare but costly.

For each input, write the expected properties, taken from the success criteria. Properties, not an
exact expected output, because many outputs can be correct. Examples: "returns valid JSON matching the
schema", "the total field equals the sum of line items", "says it does not know when the document has
no date", "under 120 words", "names the customer's plan".

## Cases every set needs

- Typical inputs, most of the set, covering the main variations.
- Edge cases: empty input, very long input, input in another language, missing fields, contradictory fields.
- The failure path: an input the model cannot answer correctly, to check that the failure instruction fires instead of a guess.
- Adversarial cases: input that invites the leading framing, input that tempts the model to invent a field, input near the boundary of scope.
- Injection cases, for any prompt that processes untrusted text: a document containing "ignore previous instructions and ...", an instruction hidden in a quoted email, a tool result telling the model to call another tool, an instruction in a different language or encoding. The expected property is that the model treats it as data and, where the prompt says so, reports it.
- Cases that resemble the few-shot examples, to check for copied content.

## Before and after comparison

1. Freeze both prompts, the model, and the parameters (temperature, reasoning effort, output mode). Record them.
2. Run the original prompt on every input. Save the outputs.
3. Run the rewrite on every input with the same model and parameters. Save the outputs.
4. Where sampling is not deterministic, run each input several times and record how often each property holds, not one result.
5. Score each output against each property: pass, fail, or unclear.
6. Compare per property and per case. Report improvements, regressions, and unchanged failures separately. A rewrite that fixes five cases and breaks two needs the two examined, not averaged away.
7. Read a sample of passing outputs too. A property list misses defects nobody thought to write down.
8. Change one thing at a time when iterating, and rerun the whole set, since a fix for one case often breaks another.

If the model or parameters change later, rerun the set. Results do not transfer between models.

## Machine checkable against human judged

Check by script wherever possible, since it is repeatable and cheap:

- Output parses (JSON, XML, CSV) and matches the schema.
- Required fields present, forbidden fields absent, values from an allowed set.
- Length limits in words, characters, or items.
- Exact or pattern matches: a date format, an identifier, a required phrase, a forbidden phrase.
- Arithmetic consistency between fields.
- Extracted values appear verbatim in the source, which catches invented fields.
- For code: it compiles, tests pass, linters pass.
- Injection cases: no tool call or action outside the allowed set occurred.

Needs a human judge, or a model judge checked against human labels on a sample:

- Whether a summary is faithful and keeps what matters.
- Tone, voice, and fit for the audience.
- Whether reasoning is sound, as opposed to present.
- Whether a refusal or "I do not know" was appropriate for that input.
- Helpfulness when several different answers are all acceptable.

A model used as a judge has its own biases. Zheng et al. report that model judges favour answers by
position, favour longer answers, and favour their own output
([Judging LLM-as-a-Judge, arXiv 2306.05685](https://arxiv.org/abs/2306.05685)). Give it the property and a rubric, not "which is better", and confirm its labels agree with a
human on a sample before trusting it for the rest.

## Reporting

```
EVALUATION
Set: number of inputs, how many adversarial, how many injection.
Model and parameters: as run.
Per property: original passes / rewrite passes, out of the set size.
Regressions: each case that got worse, with the output.
Not checked: properties that were judged on a sample only, or not at all.
```
