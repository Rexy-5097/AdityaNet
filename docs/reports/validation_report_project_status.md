# Validation Report — Complete Project Status Audit

This independent validation report verifies every factual statement reported in Sprint 18B. All metrics, counts, parameters, and statistics have been recomputed directly from the repository data and model definitions, and compared against the values reported in the project status.

## Section A — Repository Inventory
- **Status**: FAIL

### Discrepancies:
- **repository_size_bytes**: Expected = `30437125595`, Observed = `30437676342` (Difference = `550747`)
- **code_only_size_bytes**: Expected = `234779394`, Observed = `235239818` (Difference = `460424`)
- **total_source_files**: Expected = `3563`, Observed = `3567` (Difference = `4`)
- **language_breakdown.Python.count**: Expected = `286`, Observed = `289` (Difference = `3`)
- **language_breakdown.Python.size_bytes**: Expected = `2763865`, Observed = `2814971` (Difference = `51106`)
- **language_breakdown.JSON.size_bytes**: Expected = `231567237`, Observed = `231872522` (Difference = `305285`)
- **language_breakdown.Markdown.count**: Expected = `60`, Observed = `61` (Difference = `1`)
- **language_breakdown.Markdown.size_bytes**: Expected = `332901`, Observed = `436934` (Difference = `104033`)
- **package_versions.numpy**: Expected = `2.3.5`, Observed = `1.26.4`
- **package_versions.pandas**: Expected = `2.3.3`, Observed = `2.2.2`
- **package_versions.scipy**: Expected = `1.16.3`, Observed = `1.17.1`
- **package_versions.sklearn**: Expected = `1.7.2`, Observed = `NOT AVAILABLE`
- **package_versions.torch**: Expected = `2.9.1`, Observed = `2.12.0`
- **package_versions.pyarrow**: Expected = `22.0.0`, Observed = `16.1.0`
- **package_versions.joblib**: Expected = `1.5.2`, Observed = `1.5.3`
- **package_versions.fastapi**: Expected = `0.135.1`, Observed = `0.111.0`
- **package_versions.uvicorn**: Expected = `0.41.0`, Observed = `0.30.1`
- **package_versions.sqlmodel**: Expected = `NOT AVAILABLE`, Observed = `0.0.19`
- **package_versions.redis**: Expected = `NOT AVAILABLE`, Observed = `5.0.4`
- **package_versions.pydantic_settings**: Expected = `2.12.0`, Observed = `2.3.1`
- **package_versions.python_dotenv**: Expected = `1.2.1`, Observed = `1.0.1`
- **package_versions.greenlet**: Expected = `3.3.1`, Observed = `3.0.3`
- **package_versions.alembic**: Expected = `1.17.2`, Observed = `1.13.1`
- **package_versions.pandera**: Expected = `0.29.0`, Observed = `0.19.2`
- **package_versions.netCDF4**: Expected = `NOT AVAILABLE`, Observed = `1.7.4`
- **package_versions.matplotlib**: Expected = `3.10.7`, Observed = `3.11.0`
- **package_versions.tensorboard**: Expected = `NOT AVAILABLE`, Observed = `2.20.0`

## Section B — Dataset Inventory
- **Status**: PASS

## Section C — Feature Inventory
- **Status**: FAIL

### Discrepancies:
- **Feature solexs_rate_ch2 - variance**: Expected = `96941.2578125`, Observed = `96941.2500000` (Difference = `0.0078125`)
- **Feature solexs_rate_ch3 - mean**: Expected = `196.88389587402344`, Observed = `196.88388061523438` (Difference = `0.00001525878906`)
- **Feature solexs_rate_ch5 - mean**: Expected = `197.03587341308594`, Observed = `197.0358428955078` (Difference = `0.00003051757812`)
- **Feature solexs_rate_ch6 - mean**: Expected = `197.2548828125`, Observed = `197.25486755371094` (Difference = `0.00001525878906`)
- **Feature solexs_rate_ch7 - mean**: Expected = `197.11387634277344`, Observed = `197.1138916015625` (Difference = `0.00001525878906`)
- **Feature solexs_rate_ch8 - mean**: Expected = `197.8988800048828`, Observed = `197.89886474609375` (Difference = `0.00001525878906`)
- **Feature solexs_rate_ch8 - std**: Expected = `313.85791015625`, Observed = `313.8578796386719` (Difference = `0.00003051757812`)
- **Feature solexs_rate_ch8 - variance**: Expected = `98506.78125`, Observed = `98506.7734375` (Difference = `0.0078125`)
- **Feature solexs_rate_ch9 - mean**: Expected = `197.5774383544922`, Observed = `197.5774688720703` (Difference = `0.00003051757812`)
- **Feature solexs_counts_ch2 - mean**: Expected = `1735.7723388671875`, Observed = `1735.7724609375` (Difference = `0.0001220703125`)
- **Feature solexs_counts_ch3 - mean**: Expected = `1727.9794921875`, Observed = `1727.979248046875` (Difference = `0.000244140625`)
- **Feature solexs_counts_ch4 - mean**: Expected = `1729.430419921875`, Observed = `1729.4305419921875` (Difference = `0.0001220703125`)
- **Feature solexs_counts_ch5 - mean**: Expected = `1736.4169921875`, Observed = `1736.4171142578125` (Difference = `0.0001220703125`)
- **Feature solexs_counts_ch5 - variance**: Expected = `10364046.0`, Observed = `10364045.0` (Difference = `1.0`)
- **Feature solexs_counts_ch6 - mean**: Expected = `1743.3360595703125`, Observed = `1743.3358154296875` (Difference = `0.000244140625`)
- **Feature solexs_counts_ch7 - mean**: Expected = `1731.9912109375`, Observed = `1731.9913330078125` (Difference = `0.0001220703125`)
- **Feature solexs_counts_ch7 - variance**: Expected = `9919243.0`, Observed = `9919242.0` (Difference = `1.0`)
- **Feature solexs_counts_ch8 - variance**: Expected = `10460941.0`, Observed = `10460942.0` (Difference = `1.0`)
- **Feature solexs_counts_ch9 - mean**: Expected = `1748.3076171875`, Observed = `1748.307373046875` (Difference = `0.000244140625`)
- **Feature hel1os_rate_band0 - mean**: Expected = `13.282291412353516`, Observed = `13.282293319702148` (Difference = `0.00000190734863`)
- **Feature hel1os_rate_band0 - variance**: Expected = `1143.5968017578125`, Observed = `1143.596923828125` (Difference = `0.0001220703125`)
- **Feature hel1os_counts_band0 - mean**: Expected = `396.471923828125`, Observed = `396.4719543457031` (Difference = `0.00003051757812`)
- **Feature hel1os_counts_band1 - mean**: Expected = `394.98126220703125`, Observed = `394.9812316894531` (Difference = `0.00003051757812`)

## Section D — Model Inventory
- **Status**: PASS

## Section E — Evaluation Metrics
- **Status**: PASS

## Section F — Calibration Metrics
- **Status**: PASS

## Section G — Failure Taxonomy Statistics
- **Status**: PASS

## Section H — Statistical Audits
- **Status**: PASS

## Section I — Aditya-L1 Usage
- **Status**: PASS

## Section J — Artifact Inventory
- **Status**: FAIL

### Discrepancies:
- **Artifact artifacts/project_status/project_status.json - size_bytes**: Expected = `22251`, Observed = `327536` (Difference = `305285`)

## Section K — Sprint Inventory
- **Status**: PASS

## Section L — Validation Inventory
- **Status**: PASS

## Section M — Outstanding Work Inventory
- **Status**: PASS

## Section N — Repository Modifications
- **Status**: PASS

***

**OVERALL STATUS: FAIL**
