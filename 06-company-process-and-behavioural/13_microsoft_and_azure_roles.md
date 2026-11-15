# 13. Microsoft and Azure roles

Checked 15 Nov 2026. Microsoft's careers page for the hiring process was not available when I tried (the page I opened said "Page not found"). So everything below is [Anecdotal] or [Third-party]. Use it as a rough guide only.

## What candidates report for SDE 2 in India (2025 to 2026)

Sources (all [Anecdotal]): [LeetCode, SDE 2 L61/L62 India 2026](https://leetcode.com/discuss/post/7769548/microsoft-interview-experience-sde-2-l61-xdc2/), [LeetCode, SDE2 Hyderabad/Noida Mar 2026](https://leetcode.com/discuss/post/7711794/microsoft-sde2-hyderabadnoida-march-2026-n83d/), [Taro, Bengaluru](https://www.jointaro.com/interviews/companies/microsoft/experiences/software-engineer-ii-bengaluru-january-1-2025-no-offer-positive-d4461f32), [LeetCode Azure SDE 2 Hyderabad](https://leetcode.com/discuss/interview-experience/1673464/microsoft-azure-sde-2-hyderabad).

- **Entry:** recruiter message or referral, then an online coding test. One 2026 Bengaluru report: Codility test, two medium problems on arrays and strings.
- **Loop:** often 3 to 4 video rounds of about 1 hour. One Hyderabad report (late 2025): online test, 3 technical rounds, then a ~30 minute "AA round" (reported as a last, senior round).
- **What the rounds contain:** coding and DSA again and again; a low-level design (LLD) round in some loops; a manager round that mixes design and questions about the team's domain; one 2026 report had a design round for a real-time collaborative document editor.
- **Azure teams:** reports for Azure SQL and Azure Storage SDE 2 (L61) roles mention 3 rounds on the same day, back to back.
- **Time:** about 25 days to 4 weeks in two reports. Glassdoor's average of about 12 days came from only 7 reports, so do not rely on it.
- One prep guide says SDE roles at the 60+ band get full system design rounds (for example, design Azure Blob Storage). I could not verify that from candidate reports.
- I found nothing specific for levels 60 or 63.

## Levels (what the numbers mean)
- Microsoft India SDE 2 is reported as **L61/L62** in candidate posts. I did not find an official Microsoft page that lists the levels. Treat the number as reported, not official.
- With your 3.5 years, SDE 2 is the level most posts about similar experience target. [General advice]

## Simple meanings
- **LLD (low-level design):** write clean classes and methods for a small system (parking lot, library). They check names, structure, and how easy it is to add features.
- **HLD (high-level design):** draw big boxes: services, database, cache, queue. Explain why.
- **Manager round:** the future manager checks past projects and how you work in a team. This is where your behavioural stories matter.
- **AA round:** reported as the last round with a senior person. I could not confirm what the letters stand for or how it works in 2026. Ask your recruiter.

## Azure and platform roles (cloud, infrastructure)
- Roles on Azure teams (for example storage, networking, compute, SQL) are still hired as software engineers. Reports show DSA, design and team-specific depth.
- Your platform story is a good fit: provisioning platform install time cut from 5 days to 1.5 hours; Terraform stack deployment time cut by 40%; observability standard on Prometheus, Grafana and Loki; incident response.
- Expect depth questions: "How does your Terraform state work? What happens if two people apply at once? How do you roll back?" Prepare plain answers.
- Azure basics to know if the job is on Azure: resource groups, subscriptions, virtual networks, AKS (Azure Kubernetes Service), Azure Active Directory (now called Microsoft Entra ID), Azure Storage. [General advice]
- Your Google Cloud Professional Cloud Architect certificate shows cloud design thinking. It is not an Azure certificate. Say so honestly if asked.

## How to prepare (General advice)
1. Two weeks of timed DSA (mediums) plus talking out loud.
2. One LLD problem each 3 days. Write real classes, not only boxes.
3. Two HLD designs with the "5 steps": requirements, numbers, API, data and boxes, bottlenecks.
4. Prepare team-fit stories: working with other teams, learning something new fast.
5. Ask the recruiter: "Which team? Is it Azure? How many rounds? Is the last round a senior interviewer?"

## Sources
- LeetCode SDE 2 L61/L62 India 2026 [Anecdotal]: https://leetcode.com/discuss/post/7769548/microsoft-interview-experience-sde-2-l61-xdc2/
- LeetCode SDE2 Hyderabad/Noida Mar 2026 [Anecdotal]: https://leetcode.com/discuss/post/7711794/microsoft-sde2-hyderabadnoida-march-2026-n83d/
- Taro Bengaluru [Anecdotal]: https://www.jointaro.com/interviews/companies/microsoft/experiences/software-engineer-ii-bengaluru-january-1-2025-no-offer-positive-d4461f32
- Microsoft Careers (hiring process page not found when I tried): https://careers.microsoft.com
