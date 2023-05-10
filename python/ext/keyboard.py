from spreadsheetbot.sheets.keyboard import KeyboardAdapterClass

from spreadsheetbot.sheets.i18n import I18n

KeyboardAdapterClass.default_pre_async_init = KeyboardAdapterClass._pre_async_init
async def _pre_async_init(self):
    await self.default_pre_async_init()
    self.GET_CHECKLIST = I18n.get_checklist
KeyboardAdapterClass._pre_async_init = _pre_async_init

KeyboardAdapterClass.default_process_df_update = KeyboardAdapterClass._process_df_update
async def _process_df_update(self):
    await self.default_process_df_update()
    self.get_checklist_keyboard_row = self._get(self.as_df.function == self.GET_CHECKLIST)
KeyboardAdapterClass._process_df_update = _process_df_update