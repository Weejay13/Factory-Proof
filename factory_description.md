# FactoryProof

FactoryProof is a BAND-native software factory. A coordinator scopes work and recruits specialists; a builder produces a bounded change; a verifier runs independent checks; a critic can veto unsupported evidence; and a human owner controls promotion.

The product is the factory and the run it produces. The current reference case is the Pocketful track, but the factory itself is track-agnostic: its mandates can be handed to a team building a different product. The repository includes a local dashboard, a deterministic case runner, a clean-container service, stage implementations, and optional BAND role runners.

## Reference case

The reference task is a Pocketful-style wallet transfer: a transfer must be idempotent under retries, concurrent requests must not create or spend money twice, amounts must remain exact, and the service must preserve a reviewable audit trail. The official kickoff specification is authoritative for final endpoint names, response shapes, and test selectors.

## Collaboration proof

The room is load-bearing: the coordinator's plan changes the builder's work, the verifier's veto changes the next revision, and the critic's recommendation controls the human gate. The local dashboard mirrors those events so the run can be evaluated without credentials; the live BAND room is the submission evidence.
