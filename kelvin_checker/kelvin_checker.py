"""
Data Application.
"""

from kelvin.sdk.app import DataApplication
from datetime import datetime, timezone, timedelta
import time
import pytz
import os
from email.contentmanager import ContentManager
from email.message import EmailMessage
from smtplib import SMTP_SSL
import mimetypes

from kelvin_checker.checker import Checker

import pandas as pd

class App(DataApplication):
    """Application."""

    

    def init(self) -> None:
        """
        Initialization method
        """

        # Debugging code
        self.msg_count = 0
    
        assets = self.client.asset.list_asset()
        print("Name of first asset: ")
        print(assets[0].name)
        # End debugging code


        # get all configs
        asset_type= self.config.assets.type
        interval = self.config.checking.interval
        grace_interval= self.config.checking.grace_interval    
        sleep_time = self.config.execution_time.sleep
        first_metric = self.config.metrics.first_metric
        second_metric = self.config.metrics.second_metric
        result_metric = self.config.metrics.result_metric
        test_asset= self.config.assets.test_asset


        print(f'configs:\n asset_type = {asset_type}\n interval={interval}\n grace_interval = {grace_interval}\n sleep_time={sleep_time}\n first_metric={first_metric}\n second_metric={second_metric}\n result_metric={result_metric}\n test_asset={test_asset}')




        
    def process(self) -> None:
        """Process data."""
        # get all configs and env vars
        asset_type= self.config.assets.type
        interval = self.config.checking.interval
        grace_interval= self.config.checking.grace_interval    
        sleep_time = self.config.execution_time.sleep
        first_metric = self.config.metrics.first_metric
        second_metric = self.config.metrics.second_metric
        result_metric = self.config.metrics.result_metric
        test_asset= self.config.assets.test_asset
        controlchange_type=self.config.control_changes.controlchange_type

        smtp_server = os.environ.get("SMTP_SERVER")
        receiver= self.config.mail.receiver
        if self.config.mail.test_mode:
            receiver = self.config.mail.test_receiver
        receiver = receiver.split(',')
        username = os.environ.get("SMTP_USERNAME")
        password = os.environ.get("SMTP_PASSWORD")
        sender = os.environ.get("SMTP_SENDER")

        now = datetime.now()


        # Consistency check for Debugging
        if self.config.debug:
            print ("I am counting ... %d" % (self.msg_count) )
            self.msg_count += 1

            metric = self.client.storage.get_historian_metric_last(name=first_metric, asset_name=test_asset)
            print(metric.payload.get('value'))

        # End Debugging


        # Main application logic is only executed at a specific time of day
        if now.hour == self.config.execution_time.hour and now.minute == self.config.execution_time.minute:
            appname = self.config.appname
            print(f'Executing {appname} Checker')
            checker = Checker(client=self.client, first_metric=first_metric, second_metric=second_metric, results_metric=result_metric, asset_type=asset_type, controlchange_type=controlchange_type)
            metric_name = [first_metric,second_metric]
            metrics_check = checker.get_last_metrics_pivot(metric_list = metric_name, interval = interval, grace_interval=grace_interval)

            metrics_check.loc[metrics_check['speed_match']==False].to_csv('results.csv')
            # print results: only mismatches
            
            print(f'Investigating closed loop wells at {now}:\n')
            i = 0
            print("Speed missmatch (csv format)\n")
            print("Index,Asset,Recommended Speed,Pump Speed,Speed Match")
            for asset in metrics_check.index:
                if metrics_check['speed_match'][asset] == False:
                    print(f"{i},{asset},{metrics_check[metric_name[0]][asset]},{metrics_check[metric_name[1]][asset]},{metrics_check['speed_match'][asset]}")
                    i=i+1

            print('--------------------------------------------------------')


        # Sending Mail
            timezone = self.config.timezone
            mailtime = now.astimezone(pytz.timezone(timezone)).strftime("%b-%d-%Y")

            attachment_path = "results.csv"

            asset_table = ''
            for asset in metrics_check.loc[metrics_check['speed_match']==False].index.to_list():
                asset_table = asset_table + asset + '\n'

            if len(metrics_check.loc[metrics_check['speed_match']==False])>0:
                body = f"The speedchanges proposed by {appname} on {mailtime} ({timezone}) were not effective for the following wells (for details see attached CSV):\
                    \n{asset_table}"
            else:
                body = f"All speedchanges have been effective on {mailtime} ({timezone})."


            msg = EmailMessage()
            msg["Subject"] = appname +" System Check - Speed Match"
            msg["From"] = sender
            msg["To"] = receiver
            msg.set_content(body)


            mime_type, _ = mimetypes.guess_type(attachment_path)
            mime_type, mime_subtype = mime_type.split('/', 1)
            with open(attachment_path, 'rb') as ap:
                msg.add_attachment(ap.read(), maintype=mime_type, subtype=mime_subtype,filename=os.path.basename(attachment_path))

            print(f"Sending email to: {', '.join(receiver)}")

            with SMTP_SSL(smtp_server) as conn:
                conn.login(username, password)
                conn.send_message(msg, sender, receiver)


            # Write values for  Kelvin metric that corresponds to speed match

            for asset in metrics_check.index:
                asset_name = asset

                value = metrics_check['speed_match'][asset]
                speed_match = f'{value}'

                timestamp = datetime.now(timezone.utc)
                
                checker.send_metric(asset_name=asset_name, name=result_metric, data_type="raw.boolean",value = speed_match, timestamp=timestamp)

            # reset all metrics who's assets didn't receive a closed loop control change

            assets = metrics_check.index.to_list()

            data = self.client.asset.list_asset(asset_type_name=asset_type)
            all_assets = data.name
            remaining_assets = [x for x in all_assets if x not in assets]

            for asset in remaining_assets:
                asset_name = asset

                speed_match = ""

                timestamp = datetime.now(timezone.utc)

                checker.send_metric(asset_name=asset_name, name=result_metric, data_type="raw.boolean",value = speed_match, timestamp=timestamp)




            time.sleep(sleep_time)
