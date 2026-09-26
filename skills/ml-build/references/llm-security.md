# LLM and agent security

A language model cannot reliably tell instructions from data. Anything placed in its context can steer
it, and no prompt wording fixes that. The design goal is to limit what a steered model can do. The
[OWASP Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
is the reference list; retrieve the current edition, since it is revised.

## Where injected instructions come from

Direct: the user types them. Expect it and design so a user can only affect their own session and data.

Indirect: text the model reads while working. Retrieved documents, web pages, emails, support tickets,
file uploads, code comments, image text, and the output of any tool, including your own APIs when they
echo user supplied fields. A single poisoned document in a shared index reaches every user whose query
retrieves it.

Treat all of it as untrusted data. Mark it as quoted content in the prompt so the model is less likely to
follow it, and still assume that sometimes it will.

## Tools and privileges

Give each tool the narrowest scope that does the job: read only where reading is enough, one table
instead of a database connection, one mailbox folder instead of the account. Credentials belong to the
tool on the server, scoped to the current user, never placed in the prompt.

Authorise every tool call on the server against the end user's permissions. The model's request is not an
authorisation.

Require explicit human confirmation, showing the exact action and arguments, before anything irreversible
or externally visible: payments, sending messages, deleting or overwriting data, changing permissions,
publishing, and writes to shared systems.

Set limits on steps, spend and tool calls per task so a loop or a hijacked agent stops.

## Exfiltration channels

A steered model can leak data by encoding it into something the client fetches:

- A Markdown image or link whose URL carries the data in a query string, which the chat interface loads automatically.
- A tool that makes outbound HTTP requests to an arbitrary URL.
- A message, email or ticket the agent can send to an address the attacker names.

Controls: do not auto-render images or links from model output, or allow only an explicit list of
domains. Restrict outbound requests from tools to known hosts. Require confirmation before any send to a
new recipient.

## Output handling

Model output is untrusted input to whatever consumes it. Escape it before rendering as HTML, never pass it
to a shell, `eval`, or a SQL string, and validate structured output against a schema before acting on it.

## Data exposure

Retrieval must filter by the current user's permissions before results enter the context. A document the
user cannot open must not be retrievable on their behalf.

Assume the system prompt will be extracted. Put nothing in it that is secret.

Logs of prompts and completions hold personal and confidential data. Redact before storage, set a
retention period, and restrict access.

## Testing

Add injection cases to the evaluation set: instructions hidden in a retrieved document, in a tool result,
and in an uploaded file, each trying to call a tool, reveal another user's data, or emit an exfiltration
link. Pass means the harmful action did not happen, whatever the model said. Rerun them on every model,
prompt or tool change.
