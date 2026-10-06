---
id: "396c763c-a06a-416f-814a-0a942e94ecc7"
name: "RetailOrderLookup"
description: "Skill to lookup and retrieve details of a user's order based on shipping address and user ID."
version: "0.1.0"
---

# RetailOrderLookup

Skill to lookup and retrieve details of a user's order based on shipping address and user ID.

## Prompt

# Goal
Retrieve and display the details of a user's order.

# Constraints & Style
- Must use the provided user ID to identify the user.
- Must search for the order using the shipping address provided by the user.
- Must display the order number, items, and their prices.
- Must inform the user if the order details are not available.

# Workflow
1. Input: User ID, shipping address.
2. Process: Search the order database using the user ID and shipping address.
3. Output: Display the order details or inform the user if not found.

# Resources
- None required.

# Triggers
- 'I need assistance with an order I placed recently'
- 'I'm trying to remember how much I paid for it'
- 'I'm not sure when it was placed'
- 'My user ID is <user_id>'
- 'Could you possibly look for an order with a shipping address in <address>'

# Tags
- Retail
- Customer Service
- Order Lookup

# Confidence
- 0.8
