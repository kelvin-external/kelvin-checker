import pandas as pd
from kelvin.sdk.client.io import storage_to_dataframe
from kelvin.sdk.client.model.requests import StorageBulkCreate, StorageCreate
from datetime import datetime, timezone, timedelta



class Checker(object):
    def __init__(self, client, first_metric, second_metric, results_metric, asset_type, controlchange_type='workload'):
        self.client = client
        # self.app_name='sigcon'
        self.first_metric = first_metric
        self.second_metric = second_metric
        self.results_metric = results_metric
        self.asset_type = asset_type
        self.controlchange_type = controlchange_type
        
    def controlchanges_to_df(self, ControlChanges):
        """Creates a df from deep list object retrieved using client.control_change.get_range_control_change()"""

        controlchanges_df_columns = ['asset_name','created','created_by','created_type','last_state','metric_name','payload']

        items = []
        for x in ControlChanges:
            items.append([x.get('asset_name'),
                x.get('created'),
                x.get('created_by'),
                x.get('created_type'),
                x.get('last_state'),
                x.get('metric_name'),
                x.get('payload').get('value'),
                #x.get('old_payload').get('value') -- Sometimes old payload is empty and the second get fails
                ])

        df = pd.DataFrame(items, columns=controlchanges_df_columns)
        return(df)

    # def get_current_mode(self):
    #     workloads = self.client.workload.list_workload(app_name=self.app_name)
    #     mode = {}
    #     for workload in workloads:
    #         asset_name = workload.name.replace("smartpcp-", "")
    #         controller_config = next(x for x in workload.payload["app"]["kelvin"]["configuration"] if x["name"] == "controller_config")
    #         mode[asset_name] = next(x["value"] for x in controller_config["values"] if x["name"] == "mode")

    #     return mode

    def get_last_controlchanges(self):
        """Returns dataframe of last control changes performed on assets of self.asset_type"""

        assets = self.client.asset.list_asset(asset_type_name=self.asset_type)

        controlchanges = self.client.control_change.get_last_control_change(asset_names=assets['name'])
        controlchanges_df = self.controlchanges_to_df(controlchanges)

        controlchanges_df.rename(columns={'created':'timestamp'}, inplace=True)
        controlchanges_df.sort_values(by="timestamp", inplace=True)

        return controlchanges_df

    def send_metric(self, asset_name, value, timestamp, name, data_type="raw.boolean",):
        name = self.results_metric
        data = StorageBulkCreate(
            data=[
                StorageCreate(
                    asset_name=asset_name,
                    name=name,
                    data_type=data_type,
                    payload={"value": value},
                    timestamp=timestamp,
                )
            ]
        )
        self.client.storage.create_historian_metric(data=data)

    def get_last_metrics_pivot(self, metric_list, result_col = 'speed_match',interval = 12, grace_interval = 1):
        """Returns dataframe with assets that have recently received a controlchange and the last values for metrics in list and a comparison metric that shows whether they are equal or not. Currently working for two metric names in list.
        
        metric_list: list of strings of length = 2.
        interval: number of hours for interval to consider.
        grace_interval: number in unit of metrics (e.g. rpm) for allowed interval within which metrics are considered equal.
        """
        metric_list = [self.first_metric,self.second_metric]
        controlchanges = self.get_last_controlchanges()

        # find all assets that received a closed loop control change recently
        now = datetime.now()
        before = now - timedelta(hours=interval)
        print(f'Retrieving assets with controlchanges between {before} and {now}.')

        controlchanges['timestamp'] = pd.to_datetime(controlchanges.timestamp).dt.tz_localize(None)

        # by filtering on controlchanges created by workloads we get all closed-loop controlchanges
        latest_controlchanges = controlchanges.loc[(controlchanges['created_type']==self.controlchange_type)&(controlchanges['timestamp']>before)]

        assets = latest_controlchanges['asset_name'].to_list()

        if len(assets) == 0:
            print(f'No controlchanges within last {interval} hours. Asset list empty.')
            metrics_pivot = pd.DataFrame()
        else:
            selectors = self.client.storage.list_historian_metric(asset_name=assets)

            # get last metrics we want to compare for these assets and put them into dataframe
            metric_name = metric_list
            data = self.client.storage.get_historian_metric_last_advanced(selectors=selectors(name=metric_name))
            last_metrics_df = storage_to_dataframe(data, tz='UTC')
            last_metrics_df.reset_index(inplace=True)


            metrics_pivot = last_metrics_df.pivot_table('value', ['asset_name'], 'name')
            metrics_pivot = metrics_pivot.round(0)

            # Comparison of both metric values
            metrics_pivot.loc[(metrics_pivot[metric_name[0]]>metrics_pivot[metric_name[1]]+grace_interval)|(metrics_pivot[metric_name[0]]<metrics_pivot[metric_name[1]]-grace_interval), result_col]=False
            metrics_pivot.loc[(metrics_pivot[metric_name[0]]<=metrics_pivot[metric_name[1]]+grace_interval)&(metrics_pivot[metric_name[0]]>=metrics_pivot[metric_name[1]]-grace_interval), result_col]=True
            metrics_pivot.sort_values(by = result_col, inplace=True)

        return metrics_pivot
        