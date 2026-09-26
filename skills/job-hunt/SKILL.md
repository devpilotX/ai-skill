---
name: job-hunt
description: Run a job search as a targeted operation, not a volume exercise. Use when the user wants help finding a job, applying, fixing a CV, resume, LinkedIn profile or portfolio, getting past an ATS, preparing for interviews including one-way video, answering a recruiter, negotiating salary, handling an exploding or rescinded offer or reneging, checking whether a recruiter or offer is a scam, or asks why they keep getting rejected, ghosted, or no interviews. Diagnoses which funnel stage is failing before fixing anything, rewrites applications around evidence, builds a shortlist with a human route per employer, and negotiates with retrieved pay data and local pay transparency rules. For whether to take a job or change career use career-strategy. For cover letter prose that reads machine-written use human-prose. Triggers on help me find a job, fix my resume, fix my CV, ATS, cover letter, rejected, ghosted, recruiter, LinkedIn profile, portfolio, interview prep, salary negotiation, is this job a scam, reneging.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Job hunt

The failure this corrects is fixing the wrong stage of a job search: rewriting a CV forty times when
the targeting, the recruiter screen or the interviews are what is breaking. A search is a funnel with
five stages (applications, first responses, first interviews, final stages, offers), so there are four
transitions that can fail plus the quality of the offers. The first job is finding out which one is
broken.

## When to use and when to stay off

Run when the user is looking for work, applying, preparing for interviews, dealing with recruiters, or
handling and negotiating an offer.

Stay off when:

- The question is whether to take a job, change career, go freelance, or accept a counteroffer. `career-strategy` takes that decision; this skill executes it.
- The user wants a cover letter or profile rewritten so it stops reading as machine-written. `human-prose` takes the prose; this skill keeps the content and targeting.
- The user wants a CV or portfolio exported as a formatted document. `doc-forge` takes the formatting.
- The question is legal, such as whether a non-compete binds them or whether an employer broke a pay transparency law. Hand over the question for the professional named in "What this cannot do".

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. No invented employment history, dates, titles, qualifications, or metrics. Fabrication on an application can be grounds for dismissal after hiring, and this skill does not help with it.
2. Every claim on a CV needs evidence the user can defend in an interview. If they cannot explain the number, it comes out.
3. Never invent salary data or legal rules. Retrieve pay for the country, city, level and year with a link and a date, or label it an estimate. Retrieve the current pay transparency and salary history rules for the user's jurisdiction.
4. Screen for scams before the user sends documents, money or identity details. Walk through the red flags in `references/negotiation-and-conventions.md` whenever a recruiter or offer arrives unsolicited.
5. Tell the user when the market or the target is the problem instead of the documents, with evidence.

## Procedure

### Step 1, diagnose the funnel

Ask for the numbers from the last thirty days: applications sent, first responses, first interviews,
final stages, offers. The ratios locate the problem, and each problem has a different fix.

Many applications and almost no responses means the targeting or the written application is wrong, or
the applications are going into a channel with no human at the end. Volume is not the fix.

Responses but no first interview means the recruiter screen is failing. The CV already did its job by
producing the response. Look at the screening call: pay expectations out of range, work authorisation
or location answers, notice period, or a pitch that does not connect the user to the role.

Interviews but no final stages means the technical or competency answers are not landing, or the
preparation is generic.

Final stages but no offers means competition at the last step, a reference problem, or a mismatch
that only becomes visible late. Ask for feedback explicitly.

Offers but bad ones means the targeting is too low or the negotiation is being skipped.

Ghosting at any stage is normal noise in small numbers. A pattern of it at one stage is a signal about
that stage.

### Step 2, define the target precisely

Narrow to a role, a level, an industry, a geography or remote arrangement, and a company size band. A
five person company, a two hundred person company and a large enterprise want different evidence and
run different processes.

Apply work authorisation as a filter before anything else. If the user needs sponsorship, target
employers that sponsor for that role and country, and check the official register where one exists,
such as the UK Home Office register of licensed sponsors. Remote roles often still require the right
to work in a named country.

Then name the industry where the user's existing domain knowledge is worth money. Someone leaving
logistics for software is worth more to a logistics software company than to a general one.

### Step 3, build a real shortlist

Twenty to forty named employers, not job boards. Include companies not currently advertising.

For each one, find a route to a human: a specific person, a mutual connection, a community, a former
colleague. A referral usually changes how an application is processed, and it is the largest lever the
user controls. Record the route next to each name.

Check each employer and recruiter is real before engaging: the company domain on the email, the role
on the company's own careers page, and the recruiter's history. Scam patterns are in
`references/negotiation-and-conventions.md`.

### Step 4, rewrite the application around evidence

CV bullets are an action plus a quantified result. "Cut page load from 4.2 seconds to 1.1 by moving
image processing off the request path." Cut every adjective about the user and replace it with the
thing that demonstrates it. Save the situation, action, result shape for interview stories in step 5.

Mirror the vocabulary of the job description where it is honest, because the first filter is often an
applicant tracking system (ATS) keyword match and the second is a human who recognises their own
words. Use a plain layout the ATS can parse: standard headings, no text inside images, no tables for
core content.

Length, photographs, personal details and format are local conventions. A one page resume early in a
career is a US convention; two pages is common for a UK CV; academic CVs run long with publications;
German applications often use a tabular Lebenslauf with conventions of its own. Treat these as
conventions to check for the target country and sector, using `references/negotiation-and-conventions.md`.

LinkedIn profile and portfolio follow the same rule: headline says the target role, the top items show
evidence, and every project names what the user personally did.

Cover letters: three short paragraphs. Why this employer, meaning something only someone who looked
would know. What the user has done that maps to the stated problem. What they want. For prose that
reads machine-written, hand to `human-prose`.

If AI helped draft any material, every claim still has to be the user's and defensible. Some employers
ask candidates to disclose AI use or ban it in assessments; follow the employer's stated policy and
answer honestly when asked.

### Step 5, prepare for interviews with specifics

Write six stories in the situation, action, result shape, covering a conflict, a failure, a decision
made with incomplete information, something taught to someone else, something shipped under pressure,
and something they were wrong about.

For technical roles, practise out loud and against a clock.

For one-way recorded video and AI-screened interviews, practise to a camera with the same time limits,
answer the question asked in the first sentence, and check the setup beforehand. Ask whether
retakes are allowed and how the recording is assessed. Some jurisdictions regulate these tools, for
example the Illinois Artificial Intelligence Video Interview Act and New York City Local Law 144 on
automated employment decision tools; retrieve the current rules for the user's location. Ask for an
adjustment if a disability affects the format.

Take-home assignments: ask for the expected time before starting, and decide a cap in advance.
Decline or ask to be paid when the task looks like real production work for the employer, and keep a
copy of what was submitted.

Prepare questions that only someone who researched the company would ask. Rehearse the failure story
honestly.

### Step 6, negotiate

Check the rules for the user's jurisdiction first, using `references/negotiation-and-conventions.md`:

- Several US states and cities require a pay range in job postings or on request. Where a range is posted, it is the anchor, and the user can negotiate within or above it with evidence.
- Many jurisdictions ban employers from asking about salary history. Where a ban applies, the user can decline to answer.
- The EU Pay Transparency Directive, [Directive (EU) 2023/970](https://eur-lex.europa.eu/eli/dir/2023/970/oj/eng), requires employers to give candidates the starting pay or its range before the interview and bars questions about pay history. Member states had to transpose it by 7 June 2026; check the national law in force.

Where no range is disclosed and no rule applies, avoid naming the first number when possible. Where a
number is required, give a researched range with its source, anchored at the upper end of what the
data supports.

Retrieve comparable pay for the role, level, city and year, cited with a date.

Negotiate the whole package: base, bonus structure, equity with its terms, pension contribution,
holiday, notice period, remote arrangement, equipment, training budget, start date. Whether the
package is worth taking goes to `career-strategy`.

Ask for time to consider, in writing. An exploding offer with a deadline of a day or two is a pressure
tactic; ask for an extension and treat a refusal as information.

Do not resign until the offer is written and its conditions are cleared: background check, references,
right to work, and any medical or credential checks. Offers get rescinded, and a conditional offer is
not yet a job. Ask what the background check covers and when references will be contacted, and tell
current referees before they are called.

Reneging on an accepted offer has costs: the relationship with that employer and recruiter, any signed
contract terms, and sign-on repayment. Read the contract notice terms, tell the employer promptly and
in writing, and do not keep two acceptances open.

### Step 7, track and review

A table of employer, route, date contacted, stage, and next action. Review weekly, and recompute the
funnel ratios monthly.

If a stage has not moved in three weeks, the approach at that stage is wrong. Change one thing at a
time so the cause of any improvement is identifiable.

## Self-audit

- The funnel was diagnosed before anything was rewritten, and a response-without-interview pattern was treated as a screen problem.
- Work authorisation and sponsorship were applied as a targeting filter.
- Every CV claim has defensible evidence behind it, written as action plus quantified result.
- Nothing is fabricated, including dates and titles.
- Length, photo and format follow a checked local convention, not a default.
- The shortlist has a named human route per employer, and each employer and recruiter was checked for scam signs.
- Salary figures carry a source and a date, or are labelled as estimates.
- Pay transparency and salary history rules for the user's jurisdiction were checked before advising on the first number.
- The user was told not to resign until a written offer with conditions cleared.
- If the real problem is the target, that was said plainly.

## What this cannot do

It cannot guarantee interviews or offers, see inside an employer's ATS or scoring, or confirm a
recruiter is genuine beyond the checks listed. It is not legal or immigration advice:

- Employment lawyer: "The posting for (role) in (location) had no pay range and the recruiter asked my current salary. Did the employer break a pay transparency or salary history rule, and what can I do?"
- Employment lawyer: "My offer was rescinded after I resigned (or I want to withdraw my acceptance). What are my rights and liabilities under this contract and local law?"
- Immigration lawyer: "Can I start this role on my current permit, and does the employer need to sponsor me?"
- If a scam has already taken money or identity documents: report it to the bank at once and to the national fraud reporting body, such as ReportFraud.ftc.gov in the US or Action Fraud in the UK.
