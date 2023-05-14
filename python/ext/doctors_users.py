import asyncio

import pandas as pd
from spreadsheetbot.sheets.abstract import AbstractSheetAdapter

from spreadsheetbot.sheets.i18n import I18n
from spreadsheetbot.sheets.settings import Settings

from spreadsheetbot import Log

from datetime import datetime

class DoctorsUsersAdapterClass(AbstractSheetAdapter):
    def __init__(self) -> None:
        super().__init__('doctors_users', 'doctors_users', initialize_as_df=True)
        self.wks_row_pad = 2
        self.wks_col_pad = 1
    
    async def _pre_async_init(self):
        self.sheet_name = I18n.doctors_users
        self.update_sleep_time = Settings.doctors_users_update_time
        self.retry_sleep_time  = self.update_sleep_time // 2
    
    async def _get_df(self) -> pd.DataFrame:
        df = pd.DataFrame(await self.wks.get_all_records())
        df = df.drop(index = 0, axis = 0)
        df = df.loc[
            (df.user_chat_id != "") &
            (df.doctor_id != "")
        ]
        df.doctor_id = df.doctor_id.apply(str)
        return df
    
    def get_doctor_ids(self, user_chat_id: int) -> pd.Series:
        return self.as_df.loc[self.as_df.user_chat_id == user_chat_id].doctor_id

    async def write(self, user_chat_id: int|str, doctor_id: str):
        Log.info(f"Prepeared to batch write record in {self.name} with {user_chat_id=} {doctor_id=} collumns")
        while self.whole_mutex:
            Log.info(f"Halted to batch write record in {self.name} with {user_chat_id=} {doctor_id=} collumns with whole mutex")
            await asyncio.sleep(self.retry_sleep_time)
        self.mutex.append(f"{user_chat_id}\\{doctor_id}")

        record_params = {
            'datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'user_chat_id': user_chat_id,
            'doctor_id': doctor_id
        }
        tmp_df = pd.DataFrame(record_params, columns=self.as_df.columns, index=[0]).fillna('')
        if self.as_df.empty:
            self.as_df = tmp_df
        else:
            self.as_df = pd.concat([self.as_df, tmp_df], ignore_index=True)
        
        wks_row = self.as_df.shape[0] + self.wks_row_pad
        wks_update = self._prepare_batch_update([
            (wks_row, self.wks_col(key), value)
            for key, value in record_params.items()
        ])
        await self.wks.batch_update(wks_update)
        del self.mutex[self.mutex.index(f"{user_chat_id}\\{doctor_id}")]
        Log.info(f"Done to batch write record in {self.name} with {user_chat_id=} {doctor_id=} collumns")

DoctorsUsers = DoctorsUsersAdapterClass()
