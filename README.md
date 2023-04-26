smartpcp-system-checker

Central class is defined in checker.py.

> [! Attention]
> results.csv must be created inside kevlin_checker

# Uses of Kelvin Client in checker.py

Get all assets that exist on the Kelvin tenant of a specific type
```python
assets = self.client.asset.list_asset(asset_type_name=self.asset_type)
```

Get the latest control changes that were made on these assets
```python
controlchanges = self.client.control_change.get_last_control_change(asset_names=assets['name'])
```

Get the latest values for specified metrics
```python
metric_name = ['recommended_speed','pump_speed']

selectors = self.client.storage.list_historian_metric(asset_name=assets)

data = self.client.storage.get_historian_metric_last_advanced(selectors=selectors(name=metric_name))
```

Write values for a metric
```python
self.client.storage.create_historian_metric(data=data)
```

# Kelvin App Logic in smartpcp_system_checker.py

The Kelvin app has two states: initialization and process.
## Initialization
During initialization a log is created of current configuration settings. This is only a consistency check and could be removed.

## Process
The process code is executed every second (execution interval can be modified).

Process logic
1. Load all configs and environment variables
	1. It is only necessary to load the env vars for email authentication. The Kelvin Client env vars `KELVIN_URL, KELVIN_CLIENT_ID, KELVIN_CLIENT_SECRET` are loaded automatically
2. At a specific time, execute main logic based on checker object form Checker class in checker.py
	1. Create dataframe of assets where the speed check returns false and write it to results.csv
	2. Print dataframe results to stdout (will appear in logs in Kelvin Core)
	3. Send E-mail with results.csv to recipients specified app.yaml under `self.config.mail.receiver`
	4. Write results of value comparison to dedicated metric and write blank values to all assets that didn't receive a control change within specified timeframe (default is 24 h)

	# Configuration

Asset type to be evaluated (default = well)
`asset_type= self.config.assets.type`

Interval in hours for controlchanges to be considered. E.g. 23 hconsideres all controlchanges that occured within last 23 hours.
`interval = self.config.checking.interval`

Metrics are considered to be equal within +-grace_interval
`grace_interval= self.config.checking.grace_interval    `

Time application sleeps after evaluation. 60 sec is most useful.
`sleep_time = self.config.execution_time.sleep`

Both metrics to be evaluated
```
first_metric = self.config.metrics.first_metric
second_metric = self.config.metrics.second_metric
```

Metric the application writes the result of the evaluation to (must be raw.boolean)
`result_metric = self.config.metrics.result_metric`

Asset who's first_metric will be evaluated and printed periodically for debugging of Kelvin Client
`test_asset= self.config.assets.test_asset`

Type of controlchange. workload = closed loop control change; user = open loop control change
`controlchange_type=self.config.control_changes.controlchange_type`