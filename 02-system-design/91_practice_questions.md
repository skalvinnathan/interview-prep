# 91. Practice Questions (30)

How to use: pick one, set a 45-minute timer, speak out loud, and use the 7 steps from `00`. After that, open the matching design file and compare.

## Honesty note about company tags

A question is tagged to a company **only** if I found it in a public report online that names that company. All sources are third-party prep sites or candidate reports (companies do not publish their question banks), so a tag means "reported by candidates", not "guaranteed to be asked". Questions without a tag are standard practice questions (no company claim). I could not open some sources directly and say so below.

Sources:
- Google and Stripe items: aced.io (formerly Exponent) guides - https://www.aced.io/blog/google-system-design-interview and https://www.aced.io/blog/stripe-system-design-interview
- Amazon items: a search-result summary of the igotanoffer Amazon system design page, which says the questions were reported on Glassdoor - https://igotanoffer.com/en/advice/amazon-system-design-interview (the page itself returned an access error for me, so treat as second-hand and check it yourself)
- Not verified (so not tagged): a webhook delivery system and a Stripe Connect notification system were mentioned for Stripe in one search summary, but I could not confirm them on a page. I list the webhook question under the untagged section.

---

## Reported for Google (7)

1. Design a connection-degree system for a professional network (how are two people connected: 1st, 2nd, 3rd degree). *(Study: `13`, `01f`, graph ideas.)*
2. Design a logs and metrics pipeline. *(Study: `22`, `01g`.)*
3. Design a video distribution service. *(Study: `17`, `01b`.)*
4. Design a mobile image-search client (client-side design: caching, pagination, offline). *(Study: `01e`, `16`, `15`.)*
5. Design a Google-scale product such as Maps or YouTube (pick YouTube: `17`; for Maps think tiles on a CDN + routing graph).
6. Design a URL shortener. *(Study: `10`.)*
7. How would you upgrade 5,000 servers? (Rolling upgrade, batches, health checks, canary, rollback, avoiding capacity loss; link to your CI/CD and provisioner work. Study: `20`, `03`.)

## Reported for Stripe (7)

8. Design a ledger or bookkeeping service. *(Study: `18`.)*
9. Design APIs for storing transactions and a transaction log. *(Study: `18`, `01a`.)*
10. Redesign an internal authorization system across services. *(Study: `21`; think slow policy management vs fast enforcement.)*
11. Design a rate limiter. *(Study: `11`.)*
12. Design a metrics service. *(Study: `22`.)*
13. Design a distributed LRU cache. *(Study: `01e`, `01f`: LRU = hash map + doubly linked list; shard by consistent hashing; replication; hot keys.)*
14. Design an application performance monitoring (APM) system. *(Study: `22`: metrics + traces + logs, sampling.)*

Reported by the same source for Stripe: the round is 45 to 60 minutes, run on Whimsical, and focuses on problem framing, API and data-model design, failure and scale reasoning, separation of concerns, and delivery (rollout, testing, monitoring). See `00`.

## Reported for Amazon (6) (second-hand, see note above)

15. Design a parking payment system. *(Study: `18`, `19`, `01d`.)*
16. Design a monthly phone-bill processing system (batch billing at scale). *(Study: `20`, `01g`, `18` for ledger ideas.)*
17. Design an Amazon video subscription service. *(Study: `17`, `18` for subscriptions and payments.)*
18. Design a traffic signal controller. *(Think state machines, timers, failure to a safe state, fault tolerance.)*
19. Design a shopping website at a high level. *(Study: `19`, `01e`, `10`.)*
20. Design a system that assigns devices to servers. *(Think consistent hashing, load balancing, rebalancing, failure. Study: `01c`, `01f`.)*

The same sources note that Amazon SDE II design rounds can also be low-level (object-oriented) design, and that Amazon rounds include Leadership Principle questions. See `00`.

---

## Standard practice questions (no company tag)

21. Design a chat system (like WhatsApp). *(Study: `12`.)*
22. Design a news feed. *(Study: `13`.)*
23. Design a notification service. *(Study: `14`.)*
24. Design Google Drive / Dropbox. *(Study: `15`.)*
25. Design search autocomplete. *(Study: `16`.)*
26. Design an order management system with inventory (and a flash sale). *(Study: `19`.)*
27. Design a job scheduler / workflow engine (use your provisioner as the example). *(Study: `20`.)*
28. Design an API gateway with authentication and authorization (use your UAM and OIDC gateway). *(Study: `21`.)*
29. Design a webhook delivery system (at-least-once, signing, retries, replay). *(Study: `18` Step 6, `14`, `03`.)*
30. Design a CI/CD hub that builds and deploys many services (queue of builds, workers, artifact storage, secrets, rollback, multi-tenancy). Use your own CI/CD hub experience. *(Study: `20`, `15` for artifacts, `22` for build logs.)*

---

## Self-check after each practice

- Did I ask questions first and say what is out of scope?
- Did I do a quick number estimate and say what it means?
- Did I write an API with an idempotency story?
- Did I draw version 1 and then grow it?
- Did I explain at least three trade-offs with "because"?
- Did I name at least three failures and their fixes?
- Did I finish with a 6-sentence summary?
- Did I stay within 45 minutes?

## Suggested 3-week plan

| Week | Focus |
|---|---|
| 1 | `00`, `01a` to `01h`, `02`, `03`; designs `10`, `11`, `12` |
| 2 | Designs `13` to `18` (spend extra time on `18` for Stripe); one timed mock per day |
| 3 | Designs `19` to `22` (your own-work links); `90` each night; mock questions from this file, out loud, with a friend if possible |
