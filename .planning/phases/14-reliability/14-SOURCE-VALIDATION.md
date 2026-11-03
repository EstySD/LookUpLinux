# Downloaded real source batch

User corrected the unnecessary missing-input blocker and authorized public dictionary download and direct/proxy attempts. Both routes returned HTTP 200 for actual DSL, MDX ZIP and independent ECDICT CSV; matching hashes recorded in downloads/source-downloads-receipts.json. Configured host proxy is localhost:20122; source domains do not match proxy bypass settings. No credentials are recorded.

Completed command: `python .planning/phases/14-reliability/run_source_batch.py --reuse-host`.
Initial job 61155: host passed, target setup blocked by reboot-cleared /tmp snapshot. Self-contained staging fixed setup; final affected-target job 28719 finished, reusing unchanged passing host results. No active jobs. Product hashes: source-batch-manifest.json.
Reports: source-batch-report.json, host-real-dicts.json, target-real-dicts.json, provider-direct.json, provider-proxy.json. Each dictionary passes three cases per platform; each provider route reports six blocked cases. Logs use corresponding .log names. source-cleanup.json confirms clone off and proxy tunnel closed.

Live provider routes use explicit no-proxy environment or a temporary SSH reverse tunnel to the existing host proxy. Tunnel is local to the owned-clone session and closes in finally; VM started by this batch must be confirmed powered off in source-cleanup.json.

Original Phase 13 full-suite evidence remains valid for unchanged product source. Real source checks compare DSL article text and ECDICT CSV entries independently, then call production dictionary registry and translate.lookup. Downloads are external data and are not redistributed as project fixtures.
