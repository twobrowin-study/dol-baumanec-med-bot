from spreadsheetbot.sheets.i18n import I18nAdapterClass

I18nAdapterClass.default_post_async_init = I18nAdapterClass._post_async_init
async def _post_async_init(self):
    await self.default_post_async_init()
    self.doctor_analysis = [self.doctor, self.analysis]
    self.doctor_analysis_therapist = [self.doctor, self.analysis, self.therapist]
I18nAdapterClass._post_async_init = _post_async_init