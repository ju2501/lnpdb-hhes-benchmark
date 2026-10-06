# Local lab metadata dictionary

Create a blank CSV with `lnpdb-hhes lab-template`. It is saved in the Git-ignored
`data/private/` directory. No actual HHES experimental rows ship with this release.

| Fields | Meaning |
|---|---|
| `sample_id`, `batch_id` | Unique measurement/sample identity and manufacturing batch linkage |
| `cargo`, `reporter` | Keep nucleic acid type separate from the encoded reporter, e.g. `pDNA` and `GFP` |
| `il_name`, `il_smiles`, `structure_source` | Exact ionizable-lipid identity and the source used to verify it |
| `il_mol_pct` | IL molar percentage |
| `helper_lipid`, `helper_mol_pct` | Exact helper identity and molar percentage |
| `cholesterol_lipid`, `cholesterol_mol_pct` | Cholesterol/analogue identity and molar percentage |
| `peg_lipid`, `peg_mol_pct`, `peg_identity_source` | Exact PEG-lipid identity, percentage, and verification source |
| `il_to_nucleicacid_massratio` | IL mass / nucleic-acid mass; do not silently substitute total lipid mass |
| `dose_ug_nucleicacid`, `dose_basis` | Positive numeric mass in micrograms and basis such as `per_well`; do not enter mg/kg as micrograms |
| `model_type`, `model_target`, `route` | Actual cell/animal system, delivery target, and administration route |
| `mixing_method`, `aqueous_buffer`, `dialysis_buffer` | Actual preparation conditions using the pinned category spelling |
| `experiment_batching` | `individual` or `barcoded` in the pinned schema |
| `readout_method`, `readout_time_h` | Assay and positive time in hours; these are review metadata, not guaranteed model features |
| `independent_batch_count` | Optional positive integer; leave blank if not established |
| `notes` | Optional notes about missing records, uncertainties, or deviations |

All fields except `notes` and `independent_batch_count` are required for a complete
metadata row. The assessor still writes useful errors for partially filled rows.
Zero helper mol% can represent absence, using the literal helper category `None`;
an absent component is not the same as unknown identity.

Category spellings are derived from `snapshot.json`. A mismatch is reported for
review, not automatically corrected. A generic name such as `C16-PEG2000` should
not be changed to a particular ceramide or glycerol lipid without identity evidence.

After metadata checks, retain raw FCS identifiers, gating information, dose and
cell-seeding details, QC file links, and independent-repeat definitions in local
lab records. Size/PDI/EE may be useful for the case study but are not additional
features that can simply be appended to an existing checkpoint.

`assess-lab` returns exit code 2 when metadata errors exist, while writing the
review report. When metadata checks pass it returns 0, but the report still says
`prediction_ready=false` because scientific review remains necessary.
