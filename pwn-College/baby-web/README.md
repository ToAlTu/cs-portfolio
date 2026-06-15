# Baby Web

A module from [pwn.college](https://pwn.college) covering web application security through hands-on exploitation. Each level presented a running web application with a real vulnerability to find and exploit.

Rather than posting specific payloads or solutions, I've documented the thought process behind the three categories of attacks I found most instructive. Understanding *why* these vulnerabilities exist matters more than the specific strings that exploit them.

---

## Highlight 1 — SQL Injection: From Login Bypass to Schema Discovery

**The problem:** Several levels involved a web application backed by a SQL database. User input was being passed directly into database queries without sanitization, which meant I could alter the logic of the query itself rather than just providing values to it.

**My thinking:** The progression across levels forced me to go deeper each time. First I just needed to bypass a login — understanding that the query was something like `SELECT * FROM users WHERE username='X' AND password='Y'` meant I could inject logic that makes the condition always true. But later levels required actually extracting data from the database, which meant understanding UNION-based injection: appending a second SELECT statement to the original one to pull data from arbitrary tables. The final step was enumerating the database schema itself — figuring out what tables existed before I knew what to extract from them.

**The insight:** SQL injection isn't one technique — it's a family of techniques that escalate in sophistication depending on what the application exposes. Each level taught me to think about what the underlying query must look like based on the application's behavior, then work backwards to craft input that reshapes it.

---

## Highlight 2 — Blind Injection: Extracting Data You Can't See

**The problem:** One level involved a login form that was vulnerable to SQL injection, but unlike earlier levels there was no visible output — the page just said success or failure. I needed to extract a password from the database without being able to see query results directly.

**My thinking:** If I can't see output, I need to encode the data I want into something I *can* observe — in this case, whether the login succeeds or fails. By crafting a query that joins the condition I care about (does this password character equal X?) with the login condition, the success or failure of the login becomes a signal. One character at a time, I could determine the exact value stored in the database.

**The insight:** Blind injection is slower and more methodical than direct extraction but works on a much wider range of applications. It also made me realize that "not showing error messages" is not a security control — the application's behavior itself leaks information if the underlying query is unsanitized.

---

## Highlight 3 — SSRF: Using the Server Against Itself

**The problem:** Two levels involved a `/visit` endpoint that would make the server fetch a URL on my behalf. The goal was to use this to reach internal services that weren't exposed to me directly as an external user.

**My thinking:** The server trusts itself in ways it doesn't trust me. Internal endpoints that check whether a request is coming from localhost, or from a trusted internal subdomain, will accept requests from the server that they'd reject from my browser. By supplying the server a URL pointing to one of those internal endpoints, I could make the server act as my proxy into the internal network.

**The insight:** Trust boundaries in web applications are often implicit and assumed rather than enforced. A feature that seems harmless — "fetch this URL for me" — becomes a serious vulnerability when the server occupies a more privileged network position than the user. This class of vulnerability is particularly relevant in cloud and microservice architectures where many internal services communicate over a trusted internal network.
