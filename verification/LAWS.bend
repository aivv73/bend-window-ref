import Base

# A data reference can be copied without a Window owner.
# probes/reference.py checks that the actual WindowRef declaration satisfies this.
# Foreign imports cannot enter a Bend proof module, even when unused by the proof.
law copy_reference:
  for -Reference: Data
  for +ref: Reference
  Reference & Reference
