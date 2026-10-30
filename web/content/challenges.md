# Level 0: Basic Prompt Injection (Easiest)

This challenge is supposed to be relatively easy so that people can get a feel for the challenges.

Just ask it what you are looking for, aka secrets, passwords, etc.

## Model without protections

OWASP LLM01: Prompt Injection
LLM06: Sensitive Information Disclosure


# Level 1: Input Protection Challenges

## Input Injection
OWASP LLM01: Prompt Injection
LLM06: Sensitive Information Disclosure

Explore various input manipulation techniques and understand how malicious inputs can bypass filters.


# Level 2: Output Protection Challenges

## Output Protection
LLM02: Insecure Output Handling
LLM06: Sensitive Information Disclosure

Learn about output filtering and sanitization, and test your knowledge of defensive measures.

# Level 3: Advanced Prompt Engineering

## Prompt engineering and thinking protection

A hardened system prompt, and a reasoning model told to think about injection attempts before answering.

Master sophisticated prompt crafting techniques and challenge yourself with complex injection patterns.


# Level 4: Multi-Modal Injection

## Vision, Audio and Files - Multi-modal upload image/audio/pdf/json files with prompt injection

Prompt injection via describe the files

Explore image, audio or document based prompt injection attacks and test vulnerabilities in multi-modal models.

# Level 5: Function Calling Injection

## Function calling prompt injection

LLM07: Insecure Plugin Design

The agent looks users up with a `sql_query` tool. Think SQL injection.

Master function call manipulation and understand tool-use vulnerabilities.

# Level 6: Prompt-Guard Protection

## Open Source prompt protection - [Prompt-Guard](https://github.com/meta-llama/PurpleLlama/tree/main/Prompt-Guard)

Challenge advanced protection mechanisms and test your skills against enterprise-grade defenses.

# Level 7: Prompt-Goose Protection

## Open Source prompt protection - Prompt-Guard Fintuned named Prompt-Goose

Face cutting-edge AI security tools and push the boundaries of prompt injection.

# Level 8: Excessive agency code generation agent

## Code Generation and Execution

Generate and test code to solve the challenge. Be aware of sophisticated code generation attempts that may try to exploit the code generation and execution processes. Use the tools provided to you to generate and test code. Run in a sandboxed environment with limited access system.

# Level 9: DeepResearch web page injection agent

## Web Scraping and Information Retrieval

Retrieve information from the web and use the information to solve the challenge. Be aware of sophisticated web page injection attempts that may try to exploit the web scraping and information retrieval processes. The agent searches with `web_search` and reads pages with `web_scrape`, so the pages it reads become part of its prompt.

# Level 10: Hold the Fort - All protections combined

## Maximum Security Challenge

All protections combined (input validation, output protection, function calling security, Prompt-Guard, Prompt-Goose, and advanced reasoning protection). The ultimate challenge for AI security experts. Combine all techniques for maximum difficulty.
