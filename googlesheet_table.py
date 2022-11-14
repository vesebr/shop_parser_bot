import pygsheets
from pygsheets.client import Client


class GoogleTable:
    def __init__(
            self, credence_service_file: str = "", googlesheet_file_url: str = ""
    ) -> None:
        self.credence_service_file: str = credence_service_file
        self.googlesheet_file_url: str = googlesheet_file_url

    def _get_googlesheet_by_url(
            self, googlesheet_client: pygsheets.client.Client, worksheet_title: str
    ) -> pygsheets.Spreadsheet:
        """Get Google.Docs Table sheet by document url"""
        sheets: pygsheets.Spreadsheet = googlesheet_client.open_by_url(
            self.googlesheet_file_url
        )
        return sheets.worksheet_by_title(worksheet_title)

    def _get_googlesheet_client(self) -> Client:
        """It is authorized using the service key and returns the Google Docs client object"""
        return pygsheets.authorize(
            service_file=self.credence_service_file
        )

    def write_data(
            self, cell: str = "A1", value: str = "", worksheet_title: str = ""
    ) -> None:
        googlesheet_client: pygsheets.client.Client = self._get_googlesheet_client()
        wks: pygsheets.Spreadsheet = self._get_googlesheet_by_url(googlesheet_client, worksheet_title)
        try:
            wks.update_value(cell, value)
        except:
            pass

    def add_sheet(self):
        googlesheet_client: pygsheets.client.Client = self._get_googlesheet_client()
        wks: pygsheets.Spreadsheet = googlesheet_client.open_by_url(self.googlesheet_file_url)
        wks.add_worksheet("Заказы за час")
        wks.add_worksheet("Заказы за сутки")
        wks.del_worksheet(wks.sheet1)

    def write_cells(self, values, crange, worksheet_title: str = "") -> None:
        googlesheet_client: pygsheets.client.Client = self._get_googlesheet_client()
        wks: pygsheets.Spreadsheet = googlesheet_client.open_by_url(self.googlesheet_file_url)
        sheet = wks.worksheet_by_title(worksheet_title)
        sheet.update_values(crange=crange, values=values)


        # pygsheets.Cell.set_text_format("A1", "bold")
