import pandas as pd
from spreadsheetbot.sheets.abstract import AbstractSheetAdapter

from spreadsheetbot.sheets.i18n import I18n
from spreadsheetbot.sheets.settings import Settings

class DoctorsAdapterClass(AbstractSheetAdapter):
    def __init__(self) -> None:
        super().__init__('doctors', 'doctors', initialize_as_df=True)
    
    async def _pre_async_init(self):
        self.sheet_name = I18n.doctors
        self.update_sleep_time = Settings.doctors_update_time
        self.retry_sleep_time  = self.update_sleep_time // 2
    
    async def _get_df(self) -> pd.DataFrame:
        df = pd.DataFrame(await self.wks.get_all_records())
        df = df.drop(index = 0, axis = 0)
        df = df.loc[
            (df.id != "") &
            (df.display != "") &
            (df.type.isin(I18n.doctor_analysis_therapist)) &
            (df.is_active == I18n.yes)
        ]
        df.id = df.id.apply(str)
        return df
    
    def get(self, id: str) -> pd.Series:
        return self._get(self.as_df.id == id)
    
    def get_display(self, id: str) -> str:
        return self.get(id).display

    def merge(self, doctors_done: pd.Series, user_sex: str) -> pd.DataFrame:
        doctors_done_df = doctors_done.to_frame('id')
        doctors_done_df['status'] = I18n.check
        filtered_df = self.as_df.loc[self.as_df.sex.isin(['', user_sex])]
        merged_df = pd.merge(filtered_df, doctors_done_df, on='id', how='outer')
        merged_df['status'] = merged_df['status'].fillna(I18n.todo)
        return merged_df

Doctors = DoctorsAdapterClass()
