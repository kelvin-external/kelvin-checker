"""
Data Application.
"""

from kelvin.app import DataApplication


class App(DataApplication):
    """Application."""

    def init(self) -> None:
        """
        Initialization method
        """
        # 1 - To access the complete application configuration file, i.e. the contents of the 'app.yaml':
        # self.app_configuration

        # 2 - To access the application's declared inputs:
        # self.interface.inputs

        # 3 - To access the application's declared outputs:
        # self.interface.outputs

        # 4 - To access the configuration block under "app->kelvin-configuration"
        # self.config

        # 5 - Kelvin's DataApplication provides a logger by default (structlog)
        self.logger.info("Initialising")
        # self.logger.warning("This is a warning!")
        # self.logger.error("This is an error!")

        # 6 - If available, asset properties can be accessed with:
        # self.get_asset_properties(asset_name="asset-a")

    def process(self) -> None:
        """Process data."""
        # 1 - To access all input data:
        # self.data

        self.logger.info("Data", data=self.data)

        # 2 - Considering your data is defined in the inputs as 'temperature', you can access it with:
        # temperature = self.data.temperature

        # 3 - Each message carries a header that contains context information.
        # temperature_headers = temperature.header

        # 3.1 - Time of Validity, Asset Name and Type are available in the headers
        # asset_name = temperature_headers.header.asset_name
        # type = temperature_headers.header.type
        # time_of_validity = temperature_headers.header.time_of_validity

        # 4 - Build a message to emit:
        message = self.make_message(
            type="raw.float32",
            name="doubled_temperature",
            value=1.0,
            emit=False  # True for immediate emission
        )

        # 5 - Emit the message
        # self.emit(message)

