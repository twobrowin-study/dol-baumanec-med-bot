from spreadsheetbot.sheets.users import UsersAdapterClass

from spreadsheetbot import I18n, Settings, Registration, Groups, Report, Log

import pandas as pd

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from spreadsheetbot.sheets import Keyboard

from ext.doctors import Doctors
from ext.doctors_users import DoctorsUsers

UsersAdapterClass.CALLBACK_MEDCHECK_DOCTOR   = 'callback_medcheck_doctor'
UsersAdapterClass.CALLBACK_MEDCHECK_ANALYSIS = 'callback_medcheck_analysis'
UsersAdapterClass.CALLBACK_MEDCHECK_PATTERN  = 'callback_medcheck_(doctor|analysis)'
UsersAdapterClass.CALLBACK_MEDCHECK_PREFIX   = 'callback_medcheck_'

UsersAdapterClass.CALLBACK_DOCTORS_USERS_TEMPLATE = 'callback_doctors_users_{id}'
UsersAdapterClass.CALLBACK_DOCTORS_USERS_PATTERN  = 'callback_doctors_users_*'
UsersAdapterClass.CALLBACK_DOCTORS_USERS_PREFIX   = 'callback_doctors_users_'
UsersAdapterClass.callback_doctors_users = lambda self, id: self.CALLBACK_DOCTORS_USERS_TEMPLATE.format(id=id)

UsersAdapterClass.default_keyboard_key_handler = UsersAdapterClass.keyboard_key_handler
async def keyboard_key_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard_row = Keyboard.get(update.message.text)
    if keyboard_row.function == Keyboard.GET_CHECKLIST:
        await self.get_checklist(update, keyboard_row)
        return
    await self.default_keyboard_key_handler(update, context)
UsersAdapterClass.keyboard_key_handler = keyboard_key_handler

def doctor_list_list(self, doctors_df: pd.DataFrame, doctor_type: str, prefix: str = '') -> list[str]:
    return [
        f"{prefix}{row.status} {row.display}"
        for _,row in doctors_df.loc[doctors_df.type == doctor_type].iterrows()
    ]
UsersAdapterClass.doctor_list_list = doctor_list_list

def prepare_doctor_list(self, doctors_df: pd.DataFrame, doctor_type: str, prefix: str = '') -> str:
    return '\n'.join(self.doctor_list_list(doctors_df, doctor_type, prefix))
UsersAdapterClass.prepare_doctor_list = prepare_doctor_list

def therapist_should_be_next(self, doctors_df: pd.DataFrame) -> bool:
    return doctors_df.loc[
        (doctors_df.type.isin(I18n.doctor_analysis)) &
        (doctors_df.status == I18n.todo)
    ].empty
UsersAdapterClass.therapist_should_be_next = therapist_should_be_next

async def get_checklist(self, update: Update, keyboard_row: pd.Series):
    user_id = update.effective_user.id
    doctors_done = DoctorsUsers.get_doctor_ids(user_id)
    doctors_df = Doctors.merge(doctors_done, self.get(user_id)[I18n.sex])
    reply_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(I18n.do_analysis, callback_data = self.CALLBACK_MEDCHECK_ANALYSIS)],
        [InlineKeyboardButton(I18n.do_doctor,   callback_data = self.CALLBACK_MEDCHECK_DOCTOR)],
    ])
    if self.therapist_should_be_next(doctors_df):
        therapist_row = doctors_df.loc[doctors_df.type == I18n.therapist].iloc[0]
        reply_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                self.prepare_doctor_list(doctors_df, I18n.therapist),
                callback_data = self.callback_doctors_users(therapist_row.id)
            )]
        ])
    await update.message.reply_markdown(
        keyboard_row.text_markdown.format(
            doctor_checklist = self.prepare_doctor_list(doctors_df, I18n.doctor, '  '),
            analysis_checklist = self.prepare_doctor_list(doctors_df, I18n.analysis, '  '),
            therapist = self.prepare_doctor_list(doctors_df, I18n.therapist)
        ),
        reply_markup=reply_keyboard
    )
UsersAdapterClass.get_checklist = get_checklist

async def doctors_medcheck_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    callback_data = update.callback_query.data
    doctor_type = callback_data.removeprefix(self.CALLBACK_MEDCHECK_PREFIX)
    user_id = update.effective_user.id
    doctors_done = DoctorsUsers.get_doctor_ids(user_id)
    doctors_df = Doctors.merge(doctors_done, self.get(user_id)[I18n.sex])
    await update.callback_query.message.reply_markdown(
        getattr(Settings, f"{doctor_type}_message"),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{row.status} {row.display}", callback_data=self.callback_doctors_users(row.id))]
            for _,row in doctors_df.loc[doctors_df.type == getattr(I18n, doctor_type)].iterrows()
        ])
    )
UsersAdapterClass.doctors_medcheck_handler = doctors_medcheck_handler

async def doctors_users_callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    callback_data = update.callback_query.data
    doctor_id = callback_data.removeprefix(self.CALLBACK_DOCTORS_USERS_PREFIX)
    doctor = Doctors.get(doctor_id)
    reply_answer = f"{I18n.check} {doctor.display}"

    await update.callback_query.message.reply_markdown(
        Settings.doctors_done_template.format(template = reply_answer),
        reply_markup=Keyboard.reply_keyboard
    )
    reply_markup = InlineKeyboardMarkup([
        [
            button if button.callback_data != callback_data else InlineKeyboardButton(reply_answer, callback_data=callback_data)
            for button in row
        ]
        for row in update.callback_query.message.reply_markup.inline_keyboard
    ])
    try:
        await update.callback_query.edit_message_reply_markup(reply_markup)
    except Exception:
        Log.info("Got an exception while updating message reply keyboard so returning")
        return

    if doctor.type == I18n.therapist:
        await update.callback_query.message.reply_markdown(Settings.all_is_done)
        await update.callback_query.message.reply_sticker(Settings.done_sticker)
    else:
        user_id = update.effective_user.id
        doctors_done = DoctorsUsers.get_doctor_ids(user_id)
        doctors_df = Doctors.merge(doctors_done, self.get(user_id)[I18n.sex])
        doctors_df.loc[doctors_df.id == doctor_id, 'status'] = I18n.check
        if self.therapist_should_be_next(doctors_df):
            therapist_row = doctors_df.loc[doctors_df.type == I18n.therapist].iloc[0]
            therapist_text = self.prepare_doctor_list(doctors_df, I18n.therapist)
            reply_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    therapist_text,
                    callback_data = self.callback_doctors_users(therapist_row.id)
                )]
            ])
            await update.callback_query.message.reply_markdown(
                Settings.threapist_is_next_message.format(therapist=therapist_text),
                reply_markup=reply_keyboard
            )
    
    await DoctorsUsers.write(update.effective_user.id, doctor_id)
UsersAdapterClass.doctors_users_callback_handler = doctors_users_callback_handler

async def proceed_registration_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user    = self.get(update.effective_chat.id)
    state   = user.state
    save_as = user[Settings.user_document_name_field]
    registration_curr = Registration.get(state)
    registration_next = Registration.get_next(state)

    last_main_state = (state == Registration.last_main_state)
    last_state      = (state == Registration.last_state)

    state_val, save_to = self._prepare_state_to_save(update.message, registration_curr.document_link)
    if state_val == None:
        await update.message.reply_markdown(registration_curr.question, reply_markup=registration_curr.reply_keyboard)
        return

    if last_state:
        await update.message.reply_markdown(Settings.registration_complete, reply_markup=Keyboard.reply_keyboard)
        await self.get_checklist(update, Keyboard.get_checklist_keyboard_row)
    else:
        await update.message.reply_markdown(registration_next.question, reply_markup=registration_next.reply_keyboard)

    update_vals = {state: state_val}
    if last_main_state:
        update_vals['is_active'] = I18n.yes
    
    await self._batch_update_or_create_record(update.effective_chat.id, save_to=save_to, save_as=save_as, app=context.application,
        state = '' if last_state else registration_next.state,
        **update_vals
    )

    count = self.active_user_count()
    if last_main_state and self.should_send_report(count):
        Groups.send_to_all_admin_groups(
            context.application,
            Report.currently_active_users_template.format(count=count),
            ParseMode.MARKDOWN
        )
UsersAdapterClass.proceed_registration_handler = proceed_registration_handler