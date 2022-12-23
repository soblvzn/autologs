from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.dispatcher.filters import BoundFilter
from aiogram.utils.exceptions import FileIsTooBig
from datetime import datetime
import urllib.request
import asyncio
import sqlite3
import logging
import random
#################################################################################################################################
from config import *
from text_config import *
#################################################################################################################################
con = sqlite3.connect('db.db')
cur = con.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS users(
	id INTEGER,
	username TEXT,
	is_banned BOOL DEFAULT(False),
	is_TermsAccepted BOOL DEFAULT(False),
	balance INTEGER DEFAULT(0),
	earned INTEGER DEFAULT(0),
	from_refer_id INTEGER,
	get_from_referals INTEGER DEFAULT(0)
	)''')
cur.execute('''CREATE TABLE IF NOT EXISTS payment_services(
	id INTEGER,
	username TEXT,
	payment_service TEXT,
	details TEXT,
	amount INTEGER
	)''')
cur.execute('''CREATE TABLE IF NOT EXISTS logs(
	id INTEGER,
	uid INTEGER,
	username TEXT,
	download_url TEXT,
	date TIMESTAMP,
	filename TEXT,
	status BOOT DEFAULT(False)
	)''')
cur.execute('''CREATE TABLE IF NOT EXISTS withdraw(
	id INTEGER,
	uid INTEGER,
	username TEXT,
	status BOOL DEFAULT(False),
	amount INTEGER,
	payment_service TEXT,
	date TIMESTAMP,
	details TEXT
	)''')
cur.execute('''CREATE TABLE IF NOT EXISTS bysoblazn(
	lastlogid INTEGER
	)''')
class states(StatesGroup):
	upload=State()
	send_msg=State()
	msg_endcheck=State()
	add_balance=State()
	take_balance=State()
	search_user=State()
	message_to_everyone=State()
	spam_check_photo=State()
	add_photo_spam=State()
	add_photo_spam2=State()
	without_photo_spam=State()
	withdraw_details=State()
	withdraw_amount=State()
#################################################################################################################################
storage = MemoryStorage()
bot = Bot(token=tg_token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s', level=logging.INFO,)
#################################################################################################################################
SplitList = lambda sample_list, chunk_size: [sample_list[i:i+chunk_size] for i in range(0, len(sample_list), chunk_size)]
def kb_viewlog(logid,uid):
	keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
	s={'Завершить отработку':f'admin_endcheck&{logid}','Отправить сообщение':f'admin_sendmsg&{uid}','Начислить баланс':f'admin_givebalance&{uid}'}
	for x in s:
		keyboard.insert(InlineKeyboardButton(x,callback_data=s[x]))
	keyboard.add(InlineKeyboardButton('⬅Назад',callback_data=f'admin_logs_unchecked'))
	return keyboard
def kb_terms(id):
	keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
	s={'✅ Принять':f'terms_accept&{id}','📛 Отклонить':f'terms_decline&{id}'}
	for x in s:
		keyboard.insert(InlineKeyboardButton(x,callback_data=s[x]))
	return keyboard
def kb_menu(id):
	keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
	s={'📂 Загрузить логи':f'logs_upload&{id}','⏳ Логи в отработке':f'logs_unchecked&{id}','👤 Профиль':f'user_profile&{id}'}
	for x in s:
		keyboard.insert(InlineKeyboardButton(x,callback_data=s[x]))
	keyboard.add(InlineKeyboardButton('☎ Тех. Поддержка', callback_data='tp'))
	if str(id) in str(admins):
		s={'':'_','Пользователи':'admin_all_users','Логи на отработку':'admin_logs_unchecked','Заявки на вывод':'admin_requests_withdraw','Рассылка':'admin_message_to_everyone'}
		for x in s:
			keyboard.insert(InlineKeyboardButton(x,callback_data=s[x]))
	elif str(id) in str(workers):
		s={'':'_','Логи на отработку':'admin_logs_unchecked'}
		for x in s:
			keyboard.insert(InlineKeyboardButton(x,callback_data=s[x]))
	return keyboard
def kb_profile(id):
	keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
	s={'💵 Вывод средств':f'user_withdraw&{id}'}
	for x in s:
		keyboard.insert(InlineKeyboardButton(x,callback_data=s[x]))
	keyboard.add(InlineKeyboardButton('⬅Назад',callback_data='main_menu'))
	return keyboard
def kb_back():
	keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
	keyboard.add(InlineKeyboardButton('⬅Назад',callback_data='main_menu'))
	return keyboard
def kb_logs():
	cur.execute('SELECT * FROM logs WHERE status=0')
	flogs=[]
	for log in cur.fetchall(): flogs.append(
		{
		"username":log[2],
		"userid":log[1],
		"logurl":log[3],
		"logid":log[0],
		"upload_time":log[4],
		"FileName":log[5]
		}
		)
	Logs = SplitList(flogs, 8)
	Keyboards = []
	for i in range(len(Logs)):
		buttons = [buttons for buttons in SplitList([types.InlineKeyboardButton(text=f"{log['logid']} | {log['username']}", callback_data=f"admin_viewlog&{log['logid']}") for log in Logs[i]], 2)]
		buttons.append([
			types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_previouslogspage"),
			types.InlineKeyboardButton(text="🔜 Далее", callback_data="admin_nextlogspage"),
		])
		buttons.append([
			types.InlineKeyboardButton(text="⬅Назад", callback_data="main_menu")
		])

		Keyboards.append(types.InlineKeyboardMarkup(inline_keyboard=buttons))

	return Keyboards
def kb_logs_user(id):
	cur.execute(f'SELECT * FROM logs WHERE (status,uid)=(False,{id})')
	flogs=[]
	for log in cur.fetchall(): flogs.append(
		{
		"username":log[2],
		"userid":log[1],
		"logurl":log[3],
		"logid":log[0],
		"upload_time":log[4],
		"FileName":log[5]
		}
		)
	Logs = SplitList(flogs, 8)
	Keyboards = []
	for i in range(len(Logs)):
		buttons = [buttons for buttons in SplitList([types.InlineKeyboardButton(text=f"{log['logid']} | {log['username']}", callback_data=f"logs_viewlog&{log['logid']}") for log in Logs[i]], 2)]
		buttons.append([
			types.InlineKeyboardButton(text="🔙 Назад", callback_data="logs_previouslogspage"),
			types.InlineKeyboardButton(text="🔜 Далее", callback_data="logs_nextlogspage"),
		])
		buttons.append([
			types.InlineKeyboardButton(text="⬅Назад", callback_data="main_menu")
		])

		Keyboards.append(types.InlineKeyboardMarkup(inline_keyboard=buttons))

	return Keyboards
def kb_adm_user(uid):
	keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
	s={'Отправить сообщение':f'admin_sendmsg&{uid}','Выдать баланс':f'admin_givebalance&{uid}','Забрать баланс':f'admin_takebalance&{uid}'}
	for x in s:
			keyboard.insert(InlineKeyboardButton(x,callback_data=s[x]))
	cur.execute(f'SELECT is_banned FROM users WHERE id={int(uid)}')
	if cur.fetchone()[0] == 0: keyboard.insert(InlineKeyboardButton('Заблокировать',callback_data=f'admin_banuser&{uid}'))
	else: keyboard.insert(InlineKeyboardButton('Разблокировать',callback_data=f'admin_unbanuser&{uid}'))
	keyboard.insert(InlineKeyboardButton('⬅Назад',callback_data='main_menu'))
	return keyboard
def kb_user_withdraw(id):
	keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
	for x in payment_services:
		keyboard.insert(InlineKeyboardButton(status[payment_services[x].split('&')[2]]+str(x),callback_data=payment_services[x]))
	keyboard.add(InlineKeyboardButton('⬅Назад', callback_data=f'user_profile&{id}'))
	return keyboard
def kb_need_withdraw(id,ps):
	keyboard = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
	s={'Реквизиты':f'wwwithdraw_details&{id}&{ps}','Сумма вывода':f'wwwithdraw_amount&{id}&{ps}','Отправить запрос':f'wwwithdraw_send&{id}&{ps}'}
	for x in s:
		keyboard.insert(InlineKeyboardButton(x,callback_data=s[x]))
	keyboard.add(InlineKeyboardButton('⬅Назад',callback_data='user_withdraw'))
	return keyboard
def kb_withdraw():
	keyboard=InlineKeyboardMarkup(row_width=3,resize_keyboard=True)
	cur.execute('SELECT * FROM withdraw WHERE status=False')
	all_trans=cur.fetchall()
	for trans in all_trans:
		keyboard.insert(InlineKeyboardButton(f'{trans[2]} | {trans[4]} р',callback_data='wwwithdrawshow&{}'.format(trans[0])))
	keyboard.add(InlineKeyboardButton('⬅Назад',callback_data='main_menu'))
	return keyboard
def kb_withdr(id,uid):
	keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
	s={'Удачно завершить вывод':f'admwwwithdraw_success&{id}','Отклонить вывод':f'admwwwithdraw_fail&{id}'}
	for x in s:
		keyboard.insert(InlineKeyboardButton(x,callback_data=s[x]))
	keyboard.insert(InlineKeyboardButton('Написать пользователю',url='tg://user?id={}'.format(uid)))
	keyboard.insert(InlineKeyboardButton('⬅Назад',callback_data='admin_requests_withdraw'))
	return keyboard
def kb_back_logs(id):
	keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
	keyboard.add(InlineKeyboardButton('⬅Назад',callback_data=f'logs_unchecked&{id}'))
	return keyboard
def kb_back_withdraws(id):
	keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
	keyboard.add(InlineKeyboardButton('⬅Назад',callback_data=f'wwwithdrawi&{id}&true'))
	return keyboard
class IsBanned(BoundFilter):
	async def check(self, message: types.Message):
		cur.execute('SELECT is_banned FROM users WHERE id={}'.format(message.from_user.id))
		data=cur.fetchone()
		if data is not None:
			if data[0] == 1: return False
			else: return True
		else: return True
#################################################################################################################################
@dp.message_handler(IsBanned(), CommandStart())
async def start(message: types.Message):
	id=message.from_user.id
	arg = message.get_args()
	if arg == '': arg=666
	cur.execute(f'SELECT is_TermsAccepted FROM users WHERE id={message.from_user.id}')
	data=cur.fetchone()
	if data is None:
		cur.execute(f'INSERT INTO users(id,username,from_refer_id) VALUES({message.from_user.id},"{message.from_user.username}",{int(arg)})')
		con.commit()
		try:
			await bot.send_message(arg,f'У вас новый реферал!\n👤 <a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a> зарегистрировался по вашей ссылке')
		except Exception as error:
			print(error)
			await message.answer('<b>Похоже тот кто вас пригласил уже не пользуется этим ботом :(</b>')
		await message.answer(terms_text, reply_markup=kb_terms(id))
	elif data[0] == 0:
		cur.execute(f'INSERT INTO users(id,username,from_refer_id) VALUES({message.from_user.id},"{message.from_user.username}",{int(arg)})')
		con.commit()
		try:
			await bot.send_message(arg,f'У вас новый реферал!\n👤 <a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a> зарегистрировался по вашей ссылке')
		except Exception as error:
			print(error)
			await message.answer('<b>Похоже тот кто вас пригласил уже не пользуется этим ботом :(</b>')
		await message.answer(terms_text, reply_markup=kb_terms(id))
	else:
		await message.answer('<b>Вы в главном меню</b>', reply_markup=kb_menu(id))
@dp.callback_query_handler(IsBanned(), text_startswith="terms")
async def terms(call: types.CallbackQuery):
	id=call.from_user.id
	include=call.data.split("&")
	if str(include[0].split("_")[1]) == "accept":
		cur.execute('UPDATE users SET is_TermsAccepted=True')
		con.commit()
		await call.message.delete()
		await call.answer('Больших профитов!')
		await call.message.answer('<b>Вы в главном меню</b>', reply_markup=kb_menu(id))
	else:
		def kb_temp():
			keyboard=InlineKeyboardMarkup(row_width=1,resize_keyboard=True)
			s={'Хочу пользоваться ботом':'send_terms'}
			for x in s:
				keyboard.insert(InlineKeyboardButton(x,callback_data=s[x]))
			return keyboard
		await bot.edit_message_text('<b>Вы не сможете пользоваться ботом, не приняв пользовательское соглашение!</b>', call.from_user.id, call.message.message_id, reply_markup=kb_temp())
@dp.callback_query_handler(IsBanned(), text='send_terms')
async def send_terms(call: types.CallbackQuery):
	id=call.from_user.id
	await call.message.delete()
	await call.message.answer(terms_text, reply_markup=kb_terms(id))
@dp.callback_query_handler(text_startswith="logs")
async def logs(call: types.CallbackQuery, state: FSMContext):
	id=call.from_user.id
	if "upload" in str(call.data):
		await bot.edit_message_text(logs_upload_text,call.from_user.id,call.message.message_id)
		await states.upload.set()
		async with state.proxy() as data:
			data["message_to_delete"] = call.message
		dp.register_message_handler(upload_logs, state=states.upload, content_types=["text", "document"])
	elif 'unchecked' in str(call.data):
		LogsKb = kb_logs_user(id)
		if len(LogsKb) == 0:
			await call.answer(text="Логи отсутствуют")
			return
		async with state.proxy() as StateData:
			StateData["CurrentLogsPage"] = 0
			await call.message.edit_text(f"Страница {StateData['CurrentLogsPage'] + 1}/{len(LogsKb)}\nЛоги:", reply_markup=LogsKb[0])
	elif 'viewlog' in str(call.data):
		logid = int(call.data.split("&")[1])
		cur.execute(f'SELECT * FROM logs WHERE id={logid}')
		logdata = cur.fetchone()
		await call.message.edit_text(f"Дата отправки логов: <code>{datetime.fromtimestamp(logdata[4])}</code>\nLogs ID: <code>{logdata[0]}</code>\nСсылка на логи: <code>{logdata[3]}</code>", reply_markup=kb_back_logs(logdata[0]))
	elif 'nextlogspage' in str(call.data):
		LogsKb = kb_logs_user(id)
		async with state.proxy() as StateData:
			StateData["CurrentLogsPage"] += 1
			try:
				await call.message.edit_text(f"Страница {StateData['CurrentLogsPage'] + 1}/{len(LogsKb)}\nЛоги:", reply_markup=LogsKb[StateData["CurrentLogsPage"]])
			except IndexError:
				StateData["CurrentLogsPage"] = len(LogsKb) - 1
				await call.answer(text="Конец")
				return
	elif 'previouslogspage' in str(call.data):
		LogsKb = kb_logs_user(id)
		async with state.proxy() as StateData:
			StateData["CurrentLogsPage"] -= 1
			if StateData["CurrentLogsPage"] < 0:
				StateData["CurrentLogsPage"] = 0
				await call.answer(text="Начало")
				return
			await call.message.edit_text(f"Страница {StateData['CurrentLogsPage'] + 1}/{len(LogsKb)}\nЛоги:",reply_markup=LogsKb[StateData["CurrentLogsPage"]])
@dp.callback_query_handler(IsBanned(), text_startswith="admin")
async def admin(call: types.CallbackQuery, state: FSMContext):
	if 'logs_unchecked' in str(call.data):
		LogsKb = kb_logs()
		if len(LogsKb) == 0:
			await call.answer(text="Логи отсутствуют")
			return
		async with state.proxy() as StateData:
			StateData["CurrentLogsPage"] = 0
			await call.message.edit_text(f"Страница {StateData['CurrentLogsPage'] + 1}/{len(LogsKb)}\nЛоги:", reply_markup=LogsKb[0])
	elif 'nextlogspage' in str(call.data):
		LogsKb = kb_logs()
		async with state.proxy() as StateData:
			StateData["CurrentLogsPage"] += 1
			try:
				await call.message.edit_text(f"Страница {StateData['CurrentLogsPage'] + 1}/{len(LogsKb)}\nЛоги:", reply_markup=LogsKb[StateData["CurrentLogsPage"]])
			except IndexError:
				StateData["CurrentLogsPage"] = len(LogsKb) - 1
				await call.answer(text="Конец")
				return
	elif 'previouslogspage' in str(call.data):
		LogsKb = kb_logs()
		async with state.proxy() as StateData:
			StateData["CurrentLogsPage"] -= 1
			if StateData["CurrentLogsPage"] < 0:
				StateData["CurrentLogsPage"] = 0
				await call.answer(text="Начало")
				return
			await call.message.edit_text(f"Страница {StateData['CurrentLogsPage'] + 1}/{len(LogsKb)}\nЛоги:",reply_markup=LogsKb[StateData["CurrentLogsPage"]])
	elif 'viewlog' in str(call.data):
		logid = int(call.data.split("&")[1])
		cur.execute(f'SELECT * FROM logs WHERE id={logid}')
		logdata = cur.fetchone()
		await call.message.edit_text(f"Пользователь: <b><a href='tg://user?id={logdata[1]}'>{logdata[2]}</a></b>\nUser ID: <code>{logdata[1]}</code>\n\nДата отправки логов: <code>{datetime.fromtimestamp(logdata[4])}</code>\nLogs ID: <code>{logdata[0]}</code>\nСсылка на логи: <code>{logdata[3]}</code>", reply_markup=kb_viewlog(logid,logdata[1]))
	elif 'sendmsg' in str(call.data):
		uid = int(call.data.split("&")[1])
		cur.execute(f'SELECT * FROM users WHERE id={uid}')
		user=cur.fetchone()
		await call.message.edit_text(f'<b>Пользователь: @{user[1]}|<code>{user[0]}</code>\nБаланс пользователя: {user[4]}\n\nКакое сообщение хотите ему отправить?</b>')
		await states.send_msg.set()
		async with state.proxy() as data:
			data["uid"] = uid
			data["message_to_delete"] = call.message
	elif 'endcheck' in str(call.data):
		logid = int(call.data.split("&")[1])
		cur.execute(f'SELECT * FROM logs WHERE id={logid}')
		log=cur.fetchone()
		cur.execute(f'SELECT * FROM users WHERE id={log[1]}')
		user=cur.fetchone()
		await call.message.edit_text(f'<b>Пользователь: @{user[1]}|<code>{user[0]}</code>\nБаланс пользователя: {user[4]}\nLogID: <code>{logid}</code>\n\nКакое сообщение хотите ему отправить в конце отработки лога?</b>')
		await states.msg_endcheck.set()
		async with state.proxy() as data:
			data["uid"] = user[0]
			data["logid"] = log[0]
			data["message_to_delete"] = call.message
	elif 'givebalance' in str(call.data):
		uid = int(call.data.split("&")[1])
		cur.execute(f'SELECT * FROM users WHERE id={uid}')
		user=cur.fetchone()
		await call.message.edit_text(f'<b>Пользователь: @{user[1]}|<code>{user[0]}</code>\nБаланс пользователя: {user[4]}\n\nНа сколько хотите пополнить баланс пользователя?</b>')
		await states.add_balance.set()
		async with state.proxy() as data:
			data["uid"] = user[0]
			data["message_to_delete"] = call.message
	elif 'takebalance' in str(call.data):
		uid = int(call.data.split("&")[1])
		cur.execute(f'SELECT * FROM users WHERE id={uid}')
		user=cur.fetchone()
		await call.message.edit_text(f'<b>Пользователь: @{user[1]}|<code>{user[0]}</code>\nБаланс пользователя: {user[4]}\n\nСколько хотите забрать из баланса пользователя?</b>')
		await states.take_balance.set()
		async with state.proxy() as data:
			data["uid"] = user[0]
			data["message_to_delete"] = call.message
	elif 'all_users' in str(call.data):
		await call.message.edit_text(f'<b>Отправьте id или юзернейм пользователя, которого хотите найти</b>')
		await states.search_user.set()
		async with state.proxy() as data:
			data["message_to_delete"] = call.message
	elif 'message_to_everyone' in str(call.data):
		await call.message.edit_text(f'<b>Отправьте текст который хотите отправить</b>')
		await states.message_to_everyone.set()
		async with state.proxy() as data:
			data["message_to_delete"] = call.message
	elif 'unbanuser' in str(call.data):
		id=int(call.data.split('&')[1])
		if str(id) not in str(admins):
			cur.execute(f'UPDATE users SET is_banned=False WHERE id={int(id)}')
			con.commit()
			try: await bot.send_message(id, '<b>Вы были разблокированы!</b>')
			except: pass
			await call.message.edit_text(f'<b>Пользователь с ID {id} разблокирован</b>')
		else:
			await call.message.edit_text('Админа нельзя забанить, так что зачем его разблокировать?')
	elif 'banuser' in str(call.data):
		id=int(call.data.split('&')[1])
		if str(id) not in str(admins):
			cur.execute(f'UPDATE users SET is_banned=True WHERE id={id}')
			con.commit()
			try: await bot.send_message(id, '<b>Вы были заблокированы!</b>')
			except: pass
			await call.message.edit_text(f'<b>Пользователь с ID {id} заблокирован</b>')
		else:
			await call.message.edit_text('<b>Ты че ебик, зачем админа забанить хочешь?</b>')
	elif 'requests_withdraw' in str(call.data):
		await call.message.edit_text('<b>Все открытые заявки на вывод средств:</b>',reply_markup=kb_withdraw())
@dp.callback_query_handler(IsBanned(), text_startswith="user_withdraw")
async def user_withdraw(call: types.CallbackQuery, state: FSMContext):
	await call.message.edit_text(withdraw_text,reply_markup=kb_user_withdraw(call.from_user.id))
@dp.callback_query_handler(IsBanned(), text_startswith="wwwithdraw")
async def user_withdraw(call: types.CallbackQuery, state: FSMContext):
	id=call.from_user.id
	payment_service=call.data.split('&')
	if 'wwwithdrawi' in str(call.data):
		if payment_service[2] == 'false': await call.answer('📛 Платёжная система временно недоступна 📛')
		else:
			cur.execute(f'SELECT details,amount FROM payment_services WHERE (id,payment_service)=({id},"{payment_service[1]}")')
			reqs=cur.fetchone()
			if reqs is None: 
				det='Не установлено'
				am='Не установлено'
			else: 
				det=reqs[0]
				am=reqs[1]
			await call.message.edit_text(f'Платёжная система: <b>{payment_service[1]}</b>\n\nТекущие реквизиты: <code>{det}</code>\nТекущая сумма вывода: <code>{am}</code> р', reply_markup=kb_need_withdraw(id,payment_service[1]))
	elif 'details' in str(call.data):
		cur.execute(f'SELECT details FROM payment_services WHERE (id,payment_service)=({id},"{payment_service[2]}")')
		reqs=cur.fetchone()
		if reqs is None: reqs='Не установлено'
		else: reqs=reqs[0]
		await states.withdraw_details.set()
		async with state.proxy() as data:
			data['msg_1']=await call.message.edit_text(f'Отправьте реквизиты сервиса <b>{payment_service[2]}</b> на которые придёт оплата.\nТекущие: <code>{reqs}</code>')
			data['uid'] = payment_service[1]
			data['payment_service'] = payment_service[2]
	elif 'amount' in str(call.data):
		cur.execute(f'SELECT amount FROM payment_services WHERE (id,payment_service)=({id},"{payment_service[2]}")')
		reqs=cur.fetchone()
		if reqs is None: reqs='Не установлено'
		else: reqs=reqs[0]
		await states.withdraw_amount.set()
		async with state.proxy() as data:
			data['msg_1']=await call.message.edit_text(f'Отправьте сумму выплаты сервиса <b>{payment_service[2]}</b>.\nТекущая сумма: <code>{reqs}</code>')
			data['uid'] = payment_service[1]
			data['payment_service'] = payment_service[2]
	elif 'send' in str(call.data):
		cur.execute(f'SELECT * FROM payment_services WHERE (id,payment_service)=({id},"{payment_service[2]}")')
		us=cur.fetchone()
		if us is None: await call.answer('Вы не заполнили данные')
		else:
			cur.execute(f'SELECT balance FROM users WHERE id={id}')
			balik=int((cur.fetchone())[0])
			if int(us[4]) > balik: await call.answer('У вас недостаточно денежных средств на балансе')
			else:
				cur.execute('SELECT * FROM withdraw')
				cur.execute(f'INSERT INTO withdraw(id,uid,username,amount,payment_service,date,details) VALUES({len(cur.fetchall())+1},{id},"{call.from_user.username}",{us[4]},"{payment_service[2]}",{round(datetime.now().timestamp())},"{us[3]}")')
				cur.execute(f'UPDATE users SET balance={balik-int(us[4])} WHERE id={id}')
				con.commit()
				await call.message.edit_text(f'<b>Запрос на вывод средств успешно отправлен ✅</b>')
				for x in admins:
					await bot.send_message(x,f'<b>Новая заявка на вывод средств\nПользователь: @{call.from_user.username}\nID: <code>{id}</code>\nПлатёжный сервис: {payment_service[1]}\nСумма: <code>{us[4]}</code> р\nРеквизиты: {us[3]}</b>')
	elif 'show' in str(call.data):
		cur.execute('SELECT * FROM withdraw WHERE id={}'.format(payment_service[1]))
		user=cur.fetchone()
		await call.message.edit_text(f'<b>Пользователь: {user[2]}\nID: <code>{user[0]}</code>\nПлатёжная система: {user[5]}\nСумма вывода: {user[4]}\nРеквизиты для оплаты: {user[7]}\nДата отправки запроса: {user[6]}</b>',reply_markup=kb_withdr(user[0],user[1]))
@dp.callback_query_handler(IsBanned(), text_startswith="admwwwithdraw")
async def admwwwithdraw(call: types.CallbackQuery, state: FSMContext):
	id=call.from_user.id
	status=call.data.split('&')
	if 'success' in str(call.data):
		cur.execute('UPDATE withdraw SET status=True WHERE id={}'.format(status[1]))
		con.commit()
		cur.execute('SELECT uid FROM withdraw WHERE id={}'.format(status[1]))
		uid=(cur.fetchone())[0]
		await bot.send_message(uid,'Вывод завершен успешно')
		await call.message.edit_text('<b>Вы успешно завершили вывод средств</b>',reply_markup=kb_back())
	if 'fail' in str(call.data):
		cur.execute('UPDATE withdraw SET status=True WHERE id={}'.format(status[1]))
		con.commit()
		cur.execute('SELECT uid FROM withdraw WHERE id={}'.format(status[1]))
		uid=(cur.fetchone())[0]
		await bot.send_message(uid,'Вывод отклонён')
		await call.message.edit_text('<b>Вы отменили вывод средств</b>',reply_markup=kb_back())
#################################################################################################################################
@dp.callback_query_handler(IsBanned(), text='main_menu')
async def main_menu(call: types.CallbackQuery):
	id=call.from_user.id
	arg = call.message.get_args()
	if arg == '': arg=852275785
	cur.execute(f'SELECT is_TermsAccepted FROM users WHERE id={call.from_user.id}')
	data=cur.fetchone()
	if data is None:
		cur.execute(f'INSERT INTO users(id,username,from_refer_id) VALUES({call.from_user.id},"{call.from_user.username}",{int(arg)})')
		con.commit()
		try:
			await bot.send_message(arg,f'У вас новый реферал!\n👤 <a href="tg://user?id={call.from_user.id}">{call.from_user.first_name}</a> зарегистрировался по вашей ссылке')
		except Exception as error:
			print(error)
			await call.message.answer('<b>Похоже тот кто вас пригласил уже не пользуется этим ботом :(</b>')
		await call.message.answer(terms_text, reply_markup=kb_terms(id))
	if data[0] == 0:
		cur.execute(f'INSERT INTO users(id,username,from_refer_id) VALUES({call.from_user.id},"{call.from_user.username}",{int(arg)})')
		con.commit()
		try:
			await bot.send_message(arg,f'У вас новый реферал!\n👤 <a href="tg://user?id={call.from_user.id}">{call.from_user.first_name}</a> зарегистрировался по вашей ссылке')
		except Exception as error:
			print(error)
			await call.message.answer('<b>Похоже тот кто вас пригласил уже не пользуется этим ботом :(</b>')
		await call.message.answer(terms_text, reply_markup=kb_terms(id))
	else:
		await bot.edit_message_text('<b>Вы в главном меню</b>',call.from_user.id,call.message.message_id, reply_markup=kb_menu(id))
@dp.callback_query_handler(IsBanned(), text_startswith='user_profile')
async def user_profile(call: types.CallbackQuery):
	id=call.from_user.id
	cur.execute(f'SELECT * FROM users WHERE id={id}')
	user_data=cur.fetchone()
	cur.execute(f'SELECT id FROM users WHERE from_refer_id={id}')
	refs=len(cur.fetchall())
	await bot.edit_message_text(user_profile_text.format(user_data[1],user_data[0],user_data[4],user_data[5],user_data[7],refs,percentage_of_referral,botdata.username,id),call.from_user.id, call.message.message_id,reply_markup=kb_profile(id))
@dp.callback_query_handler(IsBanned(), text="tp")
async def tp(call: types.CallbackQuery):
	id=call.from_user.id
	await bot.edit_message_text(tp_text,call.from_user.id,call.message.message_id, reply_markup=kb_back())
#################################################################################################################################
@dp.message_handler(state=states.send_msg)
async def send_msgg(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		uid = data["uid"]
		msg_to_del = data["message_to_delete"]
	await state.finish()
	await message.delete()
	await msg_to_del.delete()
	try:
		await bot.send_message(uid, f'<b>Вам</b> пришло сообщение от <b>Админстратора</b>\nСодержание: <b>{message.text}</b>')
		await message.answer('✅ Сообщение успешно отправлено ✅', reply_markup=kb_back())
	except Exception as error:
		await message.answer(f'📛 Неудалось отправить сообщение 📛\n\nОшибка: <code>{error}</code>')
@dp.message_handler(state=states.msg_endcheck)
async def msg_endcheck(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		uid = data["uid"]
		logid = data["logid"]
		msg_to_del = data["message_to_delete"]
	await state.finish()
	await message.delete()
	await msg_to_del.delete()
	cur.execute(f'UPDATE logs SET status=True WHERE id={logid}')
	con.commit()
	try:
		await bot.send_message(uid, f'<b>Отработка ваших логов завершена!\nLogs ID:</b> <code>{logid}</code>\nСообщение от отработчика: <b>{message.text}</b>')
		await message.answer('✅ Сообщение успешно отправлено ✅', reply_markup=kb_back())
	except Exception as error:
		await message.answer(f'📛 Неудалось отправить сообщение 📛\n\nОшибка: <code>{error}</code>')
@dp.message_handler(state=states.add_balance)
async def add_balance(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		uid = data["uid"]
		msg_to_del = data["message_to_delete"]
	await state.finish()
	if message.text.isdigit():
		await message.delete()
		await msg_to_del.delete()
		cur.execute(f'SELECT balance,earned,from_refer_id FROM users WHERE id={uid}')
		gg=cur.fetchone()
		newbal=int(gg[0])+int(message.text)
		all_time=int(gg[1])+int(message.text)
		cur.execute(f'SELECT id,balance,earned,get_from_referals FROM users WHERE id={gg[2]}')
		another=cur.fetchone()
		an_newbal=int(another[1])+(int(message.text)*(percentage_of_referral/100))
		an_alltime=int(another[2])+(int(message.text)*(percentage_of_referral/100))
		an_fromreferals=int(another[3])+(int(message.text)*(percentage_of_referral/100))
		cur.execute(f'UPDATE users SET (balance,earned,get_from_referals)=({an_newbal},{an_alltime},{an_fromreferals}) WHERE id={another[0]}')
		cur.execute(f'UPDATE users SET (balance,earned)=({newbal},{all_time}) WHERE id={uid}')
		con.commit()
		try: bot.send_message(another[0],'<b>Вы получили с реферала <code>{}</code> р\nВаш новый баланс: <code>{}</code></b>'.format(int(message.text)*(percentage_of_referral/100),an_newbal))
		except: pass
		try:
			await bot.send_message(uid, f'<b>Ваш баланс пополнен!\nНовый баланс: <code>{newbal}</code></b>')
			await message.answer('<b>✅ Баланс пользователя пополнен ✅</b>', reply_markup=kb_back())
		except Exception as error:
			await message.answer(f'<b>📛 Неудалось пополнять баланс пользователя 📛\n\nОшибка: <code>{error}</code></b>')
	else:
		def kb_temp():
			keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
			s={'Повторить попытку':f'admin_givebalance&{uid}','⬅Назад':'main_menu'}
			for x in s:
				keyboard.insert(InlineKeyboardButton(x,callback_data=s[x]))
			return keyboard
		await message.answer('<b>📛 В сообщении присутствую посторонние символы 📛\nВведите число без посторонних символов!</b>',reply_markup=kb_temp())
@dp.message_handler(state=states.take_balance)
async def take_balance(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		uid = data["uid"]
		msg_to_del = data["message_to_delete"]
	await state.finish()
	if message.text.isdigit():
		await message.delete()
		await msg_to_del.delete()
		cur.execute(f'SELECT balance FROM users WHERE id={uid}')
		newbal=int(cur.fetchone()[0])-int(message.text)
		cur.execute(f'UPDATE users SET balance={newbal} WHERE id={uid}')
		con.commit()
		try:
			await bot.send_message(uid, f'Ваш баланс убавлен!\nНовый баланс: <code>{newbal}</code>')
			await message.answer('✅ Баланс пользователя убавлен ✅', reply_markup=kb_back())
		except Exception as error:
			await message.answer(f'📛 Неудалось убавить баланс пользователя 📛\n\nОшибка: <code>{error}</code>')
	else:
		def kb_temp():
			keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
			s={'Повторить попытку':f'admin_takebalance&{uid}','⬅Назад':'main_menu'}
			for x in s:
				keyboard.insert(InlineKeyboardButton(x,callback_data=s[x]))
			return keyboard
		await message.answer('<b>📛 В сообщении присутствую посторонние символы 📛\nВведите число без посторонних символов!</b>',reply_markup=kb_temp())
@dp.message_handler(state=states.search_user)
async def search_user(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		msg_to_del = data["message_to_delete"]
	await state.finish()
	await message.delete()
	await msg_to_del.delete()
	if message.text.isdigit():
		cur.execute(f'SELECT * FROM users WHERE id={int(message.text)}')
		user=cur.fetchone()
		ban={0:'Не заблокирован',1:'Заблокирован'}
		terms={0:'Не принял',1:'Принял'}
		if user is not None:
			await message.answer(f'Юзернейм: @{user[1]}\nID: <code>{user[0]}</code>\nСтатус: {ban[user[2]]}\nБаланс: <code>{user[4]}</code>р\nЗаработал за всё время: <code>{user[5]}</code>р\nЗаработал с рефералов: <code>{user[7]}</code>р\nПользовательское соглашение: {terms[user[3]]}\nПришёл от: <code>{user[6]}</code>', reply_markup=kb_adm_user(user[0]))
		else:
			def kb_temp():
				keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
				s={'Повторить попытку':f'admin_all_users','⬅Назад':'main_menu'}
				for x in s:
					keyboard.insert(InlineKeyboardButton(x,callback_data=s[x]))
				return keyboard
			await message.answer('<b>📛 Неудалось найти пользователя 📛</b>',reply_markup=kb_temp())
	else:
		if '@' in str(message.text): username=str(message.text.replace('@',''))
		else: username=str(message.text)
		cur.execute(f'SELECT * FROM users WHERE username="{username}"')
		user=cur.fetchone()
		ban={0:'Не заблокирован',1:'Заблокирован'}
		terms={0:'Не принял',1:'Принял'}
		if user is not None:
			await message.answer(f'Юзернейм: @{user[1]}\nID: <code>{user[0]}</code>\nСтатус: {ban[user[2]]}\nБаланс: <code>{user[4]}</code>р\nЗаработал за всё время: <code>{user[5]}</code>р\nЗаработал с рефералов: <code>{user[7]}</code>р\nПользовательское соглашение: {terms[user[3]]}\nПришёл от: <code>{user[6]}</code>', reply_markup=kb_adm_user(user[0]))
		else:
			def kb_temp():
				keyboard = InlineKeyboardMarkup(row_width=2,resize_keyboard=True)
				s={'Повторить попытку':f'admin_all_users','⬅Назад':'main_menu'}
				for x in s:
					keyboard.insert(InlineKeyboardButton(x,callback_data=s[x]))
				return keyboard
			await message.answer('<b>📛 Неудалось найти пользователя 📛</b>',reply_markup=kb_temp())
@dp.message_handler(state=states.message_to_everyone)
async def message_to_everyone(message: types.Message, state: FSMContext):
	def kb_temp():
		keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
		s=['Добавить картинку','Продолжить без картинки']
		for x in s:
			keyboard.insert(KeyboardButton(x,callback_data=x))
		return keyboard
	await states.spam_check_photo.set()
	msg=await message.answer('<b>Хотите добавить картинку?</b>', reply_markup=kb_temp())
	async with state.proxy() as data:
		data["message_to_delete"] = data["message_to_delete"]
		data["message_to_delete2"] = message
		data["message_to_delete4"] = msg
		data["text_to_send"] = str(message.text)
@dp.message_handler(state=states.spam_check_photo)
async def spam_check_photo(message: types.Message, state: FSMContext):
	if 'Добавить' in str(message.text):
		await states.add_photo_spam.set()
		async with state.proxy() as data:
			data["message_to_delete"] = data["message_to_delete"]
			data["message_to_delete2"] = data["message_to_delete2"]
			data["message_to_delete3"] = message
			data["text_to_send"] = data["text_to_send"]
			data["type"] = 'photo'
			data['message_to_delete7']=await message.answer('<b>Отправь мне картинку</b>')
	elif 'без' in str(message.text):
		await states.without_photo_spam.set()
		async with state.proxy() as data:
			data["message_to_delete"] = data["message_to_delete"]
			data["message_to_delete2"] = data["message_to_delete2"]
			data["message_to_delete3"] = message
			data["message_to_delete4"] = data["message_to_delete4"]
			data["text_to_send"] = data["text_to_send"]
			def kb_temp():
				keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
				s=['Да','Нет']
				for x in s:	keyboard.insert(KeyboardButton(x))
				return keyboard
			h=await message.answer('Вы уверены что хотите запустить рассылку с таким текстом:\n<code>{}</code>'.format(data['text_to_send']), reply_markup=kb_temp())
			j=await message.answer('Текст с разметкой будет выглядет так:\n\n{}'.format(data['text_to_send']))
			data['message_to_delete5'] = h
			data['message_to_delete6'] = j
@dp.message_handler(state=states.without_photo_spam)
async def without_photo_spam(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		await message.delete()
		await data['message_to_delete'].delete()
		await data['message_to_delete2'].delete()
		await data['message_to_delete3'].delete()
		await data['message_to_delete4'].delete()
		await data['message_to_delete5'].delete()
		await data['message_to_delete6'].delete()
	if 'Да' in str(message.text):
		async with state.proxy() as data:
			asyncio.create_task(send_message_to_user(data['text_to_send'], message.from_user.id))
	else:
		await message.answer('<b>Вы отменили рассылку</b>',reply_markup=kb_back())
	await state.finish()
@dp.message_handler(state=states.add_photo_spam, content_types=['photo','document'])
async def add_photo_spam(message: types.Message, state: FSMContext):
	name = random.randint(1,99999)
	if message.content_type == 'photo':
		await message.photo[-1].download(f'{name}.jpg')
	else:
		document_id = message.document.file_id
		file_info = await bot.get_file(document_id)
		fi = file_info.file_path
		urllib.request.urlretrieve(f'https://api.telegram.org/file/bot{tg_token}/{fi}',f'./{name}.jpg')
	await states.add_photo_spam2.set()
	async with state.proxy() as data:
		data['name'] = name
		data['message_to_delete8'] = message
		def kb_temp():
			keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
			s=['Да','Нет']
			for x in s:	keyboard.insert(KeyboardButton(x))
			return keyboard
		h=await message.answer('Вы уверены что хотите запустить рассылку с таким текстом:\n<code>{}</code>'.format(data['text_to_send']), reply_markup=kb_temp())
		j=await bot.send_photo(message.from_user.id, photo=open(f'{name}.jpg','rb'), caption='Сообщение с разметкой будет выглядет так:\n\n{}'.format(data['text_to_send']))
		data['message_to_delete5'] = h
		data['message_to_delete6'] = j
@dp.message_handler(state=states.add_photo_spam2)
async def add_photo_spam2(message: types.Message, state: FSMContext):
	if 'Да' in str(message.text):
		async with state.proxy() as data:
			await message.delete()
			await data['message_to_delete'].delete()
			await data['message_to_delete2'].delete()
			await data['message_to_delete3'].delete()
			await data['message_to_delete4'].delete()
			await data['message_to_delete5'].delete()
			await data['message_to_delete6'].delete()
			await data['message_to_delete7'].delete()
			await data['message_to_delete8'].delete()
			asyncio.create_task(send_message_to_user_photo(data['text_to_send'], data['name'], message.from_user.id))
	else:
		await message.answer('Вы отменили рассылку')
	await state.finish()
@dp.message_handler(state=states.withdraw_details)
async def withdraw_details(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		await message.delete()
		await data['msg_1'].delete()
		id=data['uid']
		ps=data['payment_service']
		cur.execute(f'SELECT * FROM payment_services WHERE (id,payment_service)=({int(id)},"{str(ps)}")')
		if cur.fetchone() is None: cur.execute(f'INSERT INTO payment_services(id,username,payment_service,details) VALUES({message.from_user.id},"{message.from_user.username}","{ps}","{message.text}")')
		else: cur.execute(f'UPDATE payment_services SET details="{message.text}" WHERE (id,payment_service)=({int(id)},"{str(ps)}")')
		con.commit()
		await message.answer('Значение успешно изменено!',reply_markup=kb_back_withdraws(ps))
	await state.finish()
@dp.message_handler(state=states.withdraw_amount)
async def withdraw_amount(message: types.Message, state: FSMContext):
	if message.text.isdigit():
		async with state.proxy() as data:
			await message.delete()
			await data['msg_1'].delete()
			id=data['uid']
			ps=data['payment_service']
			cur.execute(f'SELECT amount FROM payment_services WHERE (id,payment_service)=({int(id)},"{str(ps)}")')
			if cur.fetchone() is None: cur.execute(f'INSERT INTO payment_services(id,username,payment_service,amount) VALUES({message.from_user.id},"{message.from_user.username}","{ps}",{int(message.text)})')
			else: cur.execute(f'UPDATE payment_services SET amount={int(message.text)} WHERE (id,payment_service)=({int(id)},"{str(ps)}")')
			con.commit()
		await message.answer('Значение успешно изменено!',reply_markup=kb_back_withdraws(ps))
	else:
		async with state.proxy() as data:
			await message.delete()
			await data['msg_1'].delete()
			ps=data['payment_service']
			await message.answer('<b>Отправьте число без посторонних символов</b>',reply_markup=kb_back_withdraws(ps))
	await state.finish()
#################################################################################################################################
async def send_message_to_user(text_to_send, from_userid):
	clear_address = InlineKeyboardMarkup()
	clear_address.add(InlineKeyboardButton(text="📢 Новостной канал", url="t.me/logscheker_news"))
	cur.execute('SELECT id FROM users')
	ids=cur.fetchall()
	await bot.send_message(from_userid,f'<b>Рассылка успешна запущена!\nПользователей в боте: <code>{len(ids)}</code></b>')
	receive_users=0
	block_users=0
	for id in ids:
		try:
			await bot.send_message(id[0], text_to_send, reply_markup=clear_address)
			receive_users += 1
		except Exception as error:
			print(error)
			block_users += 1
		await asyncio.sleep(0.05)
	await bot.send_message(from_userid,f"<b>📢 Рассылка была завершена ☑</b>\n<b>👤 Получили сообщение:</b> <code>{receive_users} ✅</code>\n<b>👤 Заблокировали бота:</b> <code>{block_users} ❌</code>")
async def send_message_to_user_photo(text_to_send, photo, from_userid):
	clear_address = InlineKeyboardMarkup()
	clear_address.add(InlineKeyboardButton(text="📢 Новостной канал", url="t.me/logscheker_news"))
	receive_users, block_users = 0, 0
	cur.execute('SELECT id FROM users')
	ids=cur.fetchall()
	for id in ids:
		try:
			await bot.send_photo(id[0], photo = open(f'{photo}.jpg', 'rb'),caption = text_to_send, reply_markup=clear_address)
			receive_users += 1
		except Exception as e:
			print(e)
			block_users += 1
		await asyncio.sleep(0.05)
	await bot.send_message(from_userid,f"<b>📢 Рассылка была завершена ☑</b>\n<b>👤 Получили сообщение:</b> <code>{receive_users} ✅</code>\n<b>👤 Заблокировали бота:</b> <code>{block_users} ❌</code>")
async def upload_logs(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		message_to_delete = data["message_to_delete"]
	await message.delete()
	await message_to_delete.delete()
	await state.finish()
	id=message.from_user.id
	if message.content_type == "document":
		try:
			file = await bot.get_file(message.document.file_id)
			ServerPath = file.file_path
			ServerFilename = ServerPath.split("/")[-1]
			LogURL = f"https://api.telegram.org/file/bot{tg_token}/{ServerPath}"
			if not message.document.file_name.lower().endswith(".zip"):
				await message.answer("Пожалуйста, отправьте .zip архив")
				return
		except FileIsTooBig:
			await message.answer("Пожалуйста, отправьте архив весом до 20мб")
			return
	elif message.content_type == "text":
		LogURL = message.text
		ServerFilename = None
		if not LogURL.startswith("http") or not LogURL.startswith("https"):
			await message.answer("Пожалуйста, отправьте ссылку на логи, или архив с логами в формате .zip весом до 20мб")
			return
	cur.execute('SELECT lastlogid FROM bysoblazn')
	lastlogid=(cur.fetchone())[0]
	upload_time=round(datetime.now().timestamp())
	if ServerFilename == None: message_to_sent=f"Загружены новые логи!\nСсылка на логи: <a href='{LogURL}'>{LogURL}</a>\n\nLogID: <code>{lastlogid}</code>\nПользователь: <a href='tg://user?id={id}'>@{message.from_user.username}</a>\nUser ID: <code>{id}</code>"
	else: message_to_sent=f"Загружены новые логи!\nСсылка на логи: <b><a href='{LogURL}'>клик</a></b>\nИмя файла: <code>{ServerFilename}</code>\n\nLogID: <code>{lastlogid}</code>\nПользователь: <a href='tg://user?id={id}'>@{message.from_user.username}</a>\nUser ID: <code>{id}</code>"
	cur.execute(f'UPDATE bysoblazn SET lastlogid={lastlogid+1}')
	cur.execute(f'INSERT INTO logs(id,uid,username,download_url,date,filename) VALUES ({lastlogid+1},{id},"{message.from_user.username}","{LogURL}",{upload_time},"{ServerFilename}")')
	con.commit()
	for x in admins:
		await bot.send_message(x,message_to_sent)
	await message.answer(f"Логи загружены!\n\nLogID: <code>{lastlogid}</code>", reply_markup=kb_back())
#################################################################################################################################
async def on_startup(dp):
	async def set_default_commands(dp):
		await dp.bot.set_my_commands([types.BotCommand("start", "Запустить бота")])
	await set_default_commands(dp)
	global botdata
	botdata = await bot.get_me()
	cur.execute('SELECT lastlogid FROM bysoblazn')
	for id in admins:
		await bot.send_message(id, '<b>✅ Бот был успешно запущен</b>\n➖➖➖➖➖➖➖➖➖➖\n<b>Разработчик: @soblazncc</b>')
	if cur.fetchone() is None:
		cur.execute('INSERT INTO users(id,username,from_refer_id) VALUES (666,"bysoblazn",852275785)')
		cur.execute('INSERT INTO bysoblazn(lastlogid) VALUES(0)')
		con.commit()
if __name__ == '__main__':
	executor.start_polling(dp, on_startup=on_startup)