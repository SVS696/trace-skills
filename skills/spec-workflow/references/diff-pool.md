# Revmux correction pool

For new specifications a pool exists only after a complete revmux result and its
simplicity adjudication. Authoring/integration/preflight do not create pools.

Example (stage is the final article stage, not the location of a source block):

```json
{"schema":1,"stage":4,"items":[{"id":"D4-001","source_finding_id":"F-1","target":"article.md#RULE-1","change":"Correct the transition in the final article; synchronize the named block if needed","reason":"The reviewed article contains the wrong transition","status":"open"}]}
```

Every accepted finding is covered; dismissed and invented findings are excluded.
The primary target is always the reviewed article. Correcting a block alone leaves
the finding unresolved. Supporting edits belong to the same named correction.

1. Fix the complete batch and run deterministic checks.
2. Record applied receipts with resolve-review --item ID --receipt RECEIPT. Receipts
   bind the updated article bytes. They are evidence of application, not verification.
3. Register article-updated and run the next ordinary revmux. A healthy clean round
   records confirmation. No separate targeted verification or verify-review is used.
4. A waiver requires an actual user/project decision. It does not prove the fix.

Existing cases may contain legacy stage pools and verification receipts. Their
commands remain readable for compatibility; do not create a new case in that model
or migrate existing cases without a request. Delivery pools belong to delivery-workflow.
