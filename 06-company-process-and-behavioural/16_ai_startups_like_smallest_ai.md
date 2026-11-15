# 16. AI startups like Smallest AI

Checked 15 Nov 2026. I could find only a few candidate reports for Smallest AI and nothing official about its interview steps.

## What I could verify

- Smallest AI's careers page talks about culture and links to a job board (Ashby). Values on the page: pursue the truth, own the outcome, turn research into impact. It prefers moving fast and working through unclear problems, and judges people by impact more than title. It says nothing about interview steps. [Official, via page summary of https://smallest.ai/careers]
- Glassdoor reports for Smallest AI (Bengaluru, 2025) [Anecdotal]:
  - One candidate: applied online, process took about 1 week, was asked why they want to join the company. Full-stack candidate: build a task-management web app with filtering, sorting and drag-and-drop, then basic JavaScript questions. ([Glassdoor](https://www.glassdoor.ie/Interview/smallest-ai-Full-Stack-Developer-Interview-Questions-EI_IE11064866.0,11_KO12,32.htm))
  - Another candidate: an assignment round where they were told to "vibe code" one use case for the company's models and submit three MVPs with a slide deck. ([Glassdoor](https://www.glassdoor.com.au/Interview/smallest-ai-Interview-E11064866-RVW103067663.htm))
- **I found nothing about an AI interviewer at Smallest AI.** I cannot say whether you will get one. Read the invite email.

Tiny sample. Treat it as a hint, not a rule.

## Why AI startups interview differently (General advice, not verified for Smallest AI)
- Small teams. They want someone who can finish things alone.
- They test **fundamentals** (the basics, in depth) more than big-company tricks: how does HTTP work, what is a process vs a thread, what happens when you type a URL, what is a database index, how does a queue work, how do you debug a slow service.
- They often use a **take-home or live build**: you build a small working thing in hours. Judged on: does it run, is it simple, did you think about users.
- They ask "what would you ship first?" and "what would break at 10x load?"
- Pace is fast: 3 to 5 calls in 1 to 2 weeks.

## How to prepare for a fundamentals-heavy technical call
Explain each in 60 seconds, out loud, in simple words:
1. What happens when you type a URL in the browser (DNS, TCP, TLS, HTTP, server, response).
2. Process vs thread. What is a deadlock?
3. What is an index in a database? When does it hurt?
4. REST vs gRPC. What is a webhook?
5. How does a message queue help? What if a message is delivered twice? (idempotency, see file 12)
6. What is a container? What does Kubernetes do? (You know this well from your platform work.)
7. How do you find why a service is slow? (metrics, logs, traces; your Prometheus/Grafana/Loki standard is a real example.)
8. Python or Go basics: what is a goroutine, what is the GIL (only if you list them).

For an AI company, also know simply: what an LLM is, what a prompt is, what latency means for a voice model (time to first sound), what streaming means. You do not need to be a researcher for an SDE role. [General advice]

## Take-home or "vibe coding" assignments
- "Vibe coding" means building fast with the help of an AI assistant. They still judge **your** decisions.
- Plan: (1) Read the task twice. (2) Write down what "done" means in 5 lines. (3) Build the smallest working version first. (4) Then add polish. (5) Write a short README: what you built, what you left out, why.
- If they ask for slides, 5 slides is enough: problem, what I built, demo, what I'd do next, risks.
- Do not copy blindly from the AI. Read what it wrote. Be ready to explain every part.

## AI-interviewer rounds: how to handle them
**Meaning:** a software agent asks you questions (by voice or video) and scores or summarises your answers. A human may read the result later.

What the web guides agree on (all vendor or prep sites with a commercial interest, so [Third-party]; for example [Upwork guide](https://www.upwork.com/resources/ai-interview-guide), [Hakia](https://hakia.com/news/ai-interviews-how-to-prepare/)):
- Treat it like a real interview. Dress and sit as you would for a person.
- Avoid sounding scripted.
- Check camera, mic, internet and the link before.
- Practise on a similar tool.
- Claims that these tools judge your face or body language are not independently confirmed. Do not worry about that. Focus on clear answers.

My plain advice [General advice]:
1. **Answer in a clear structure.** For behavioural questions use STAR. For technical ones: "Short answer first, then how it works, then an example."
2. **Speak slowly.** A speech-to-text system may mishear fast speech. Short sentences help. This is also good for you because English is your second language.
3. **Use specific words and numbers.** Say "install time went from 5 days to 1.5 hours", not "it got much faster".
4. **If you do not understand a question, say "Could you repeat that?"** It is fine.
5. **Do not pause for too long.** If you need time, say "Let me think for a moment."
6. **Keep each answer 1 to 2 minutes.**
7. **Ask the recruiter beforehand:** "Is a human watching? Can I retake a question? How long is the round?"
8. Check the company's privacy note. Some places (for example Illinois in the USA) require notice and consent before AI analyses video interviews. Check what the invitation says about recording. [Third-party, from search summary]

## Sources
- Smallest AI careers [Official]: https://smallest.ai/careers
- Glassdoor Smallest AI full-stack [Anecdotal]: https://www.glassdoor.ie/Interview/smallest-ai-Full-Stack-Developer-Interview-Questions-EI_IE11064866.0,11_KO12,32.htm
- Glassdoor Smallest AI assignment [Anecdotal]: https://www.glassdoor.com.au/Interview/smallest-ai-Interview-E11064866-RVW103067663.htm
- Upwork AI interview guide [Third-party]: https://www.upwork.com/resources/ai-interview-guide
- Hakia [Third-party]: https://hakia.com/news/ai-interviews-how-to-prepare/
