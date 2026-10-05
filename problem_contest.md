# Problem Contest

## Problem Statement

The repository points to a WhatsApp-based message processing system that needs to decide how to respond to incoming messages using a layered workflow. The core problem is to reliably convert a raw WhatsApp message into the right reply behavior by combining deterministic rules, memory of prior conversations, relationship context, and persona-aware response generation.

## What the Repository Shows

The repository contains two main signals:

- Chat transcripts across different relationships and contexts, including family, friends, and professional communication.
- An architecture diagram that describes a pipeline:
  - WhatsApp message input
  - Rule-based logic with number and relationship lookup
  - Hard rules
  - Signal rules
  - Intent check
  - Reply policy
  - History retrieval through ChromaDB
  - Persona context injection
  - LLM generation
  - Human-like delay
  - Final message send

## Why This Is a Problem

WhatsApp replies are not only about language generation. The system has to preserve social context, avoid inappropriate tone, and respond differently depending on who sent the message and what the conversation history says. Without this, the same incoming message could trigger the wrong response style, the wrong priority, or the wrong level of personalization.

## Key Challenges

- Identify the sender and map them to the correct relationship category.
- Apply hard rules before any flexible reasoning.
- Use history only when it is relevant and safe to use.
- Inject persona context so replies remain consistent with the intended identity.
- Control reply timing so the system feels natural rather than robotic.
- Avoid mixing personal, academic, and professional context in ways that create confusion.

## Expected Outcome

A working solution should take an incoming WhatsApp message and route it through a clear decision pipeline that:

1. Resolves sender identity and relationship.
2. Applies deterministic rules.
3. Checks intent and reply policy.
4. Retrieves useful history when needed.
5. Applies persona context.
6. Generates the final reply with human-like timing.

## Summary

In short, the problem is to build a reliable WhatsApp reply orchestration system that balances rule-based control with contextual intelligence, so responses are appropriate, consistent, and socially aware.
