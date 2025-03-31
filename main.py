import os
import logging
import sqlite3
import asyncio
from datetime import datetime
from typing import Union, Dict, Any, List

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.markdown import hbold, hitalic
from aiogram.utils.keyboard import InlineKeyboardBuilder

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from dotenv import load_dotenv

# Загружаем переменные среды из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токена бота из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("Не задан токен бота. Создайте .env файл с BOT_TOKEN=ваш_токен")

# Список администраторов (их ID в Telegram)
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(',')))
if not ADMIN_IDS:
    logger.warning("Список администраторов пуст! Добавьте ID администраторов в .env файл")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Инициализация планировщика
scheduler = AsyncIOScheduler()

# Определение состояний FSM для сценариев отправки
class SendMessageStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_schedule_time = State()
    confirm_sending = State()

# Функции для работы с базой данных
def init_db():
    """Инициализация базы данных и создание таблиц, если их нет"""
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    
    # Создаем таблицу подписчиков
    c.execute('''
    CREATE TABLE IF NOT EXISTS subscribers (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Создаем таблицу для запланированных сообщений
    c.execute('''
    CREATE TABLE IF NOT EXISTS scheduled_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_type TEXT,
        message_content TEXT,
        media_id TEXT,
        caption TEXT,
        scheduled_time TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        status TEXT DEFAULT 'pending'
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")

def add_subscriber(user_id, username, first_name, last_name):
    """Добавляет пользователя в список подписчиков"""
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    
    c.execute('''
    INSERT OR REPLACE INTO subscribers (user_id, username, first_name, last_name)
    VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name))
    
    conn.commit()
    conn.close()
    logger.info(f"Пользователь {user_id} ({username}) подписался на рассылку")

def remove_subscriber(user_id):
    """Удаляет пользователя из списка подписчиков"""
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    
    c.execute('DELETE FROM subscribers WHERE user_id = ?', (user_id,))
    
    conn.commit()
    conn.close()
    logger.info(f"Пользователь {user_id} отписался от рассылки")

def get_all_subscribers():
    """Возвращает список всех подписчиков"""
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    
    c.execute('SELECT user_id FROM subscribers')
    subscribers = [row[0] for row in c.fetchall()]
    
    conn.close()
    return subscribers

def count_subscribers():
    """Возвращает количество подписчиков"""
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM subscribers')
    count = c.fetchone()[0]
    
    conn.close()
    return count

def is_subscribed(user_id):
    """Проверяет, подписан ли пользователь"""
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM subscribers WHERE user_id = ?', (user_id,))
    count = c.fetchone()[0]
    
    conn.close()
    return count > 0

def add_scheduled_message(message_type, message_content, media_id, caption, scheduled_time, created_by):
    """Добавляет запланированное сообщение в базу данных"""
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    
    c.execute('''
    INSERT INTO scheduled_messages 
    (message_type, message_content, media_id, caption, scheduled_time, created_by)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (message_type, message_content, media_id, caption, scheduled_time, created_by))
    
    message_id = c.lastrowid
    
    conn.commit()
    conn.close()
    logger.info(f"Добавлено запланированное сообщение #{message_id} на {scheduled_time}")
    return message_id

def get_scheduled_messages(status='pending'):
    """Получает список запланированных сообщений с указанным статусом"""
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    
    c.execute('''
    SELECT id, message_type, message_content, media_id, caption, scheduled_time
    FROM scheduled_messages
    WHERE status = ?
    ORDER BY scheduled_time
    ''', (status,))
    
    messages = c.fetchall()
    
    conn.close()
    return messages

def update_message_status(message_id, status):
    """Обновляет статус запланированного сообщения"""
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    
    c.execute('''
    UPDATE scheduled_messages
    SET status = ?
    WHERE id = ?
    ''', (status, message_id))
    
    conn.commit()
    conn.close()
    logger.info(f"Обновлен статус сообщения #{message_id} на {status}")

# Вспомогательные функции
def is_admin(user_id):
    """Проверяет, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

async def send_message_to_subscribers(message_type, content, media_id=None, caption=None):
    """Отправляет сообщение всем подписчикам"""
    subscribers = get_all_subscribers()
    sent_count = 0
    failed_count = 0
    
    for user_id in subscribers:
        try:
            if message_type == 'text':
                await bot.send_message(user_id, content)
            elif message_type == 'photo':
                if media_id.startswith('file://'):
                    # Если это локальный файл
                    local_path = media_id.replace('file://', '')
                    photo = FSInputFile(local_path)
                    await bot.send_photo(user_id, photo, caption=caption)
                else:
                    # Если это file_id
                    await bot.send_photo(user_id, media_id, caption=caption)
            elif message_type == 'video':
                if media_id.startswith('file://'):
                    # Если это локальный файл
                    local_path = media_id.replace('file://', '')
                    video = FSInputFile(local_path)
                    await bot.send_video(user_id, video, caption=caption)
                else:
                    # Если это file_id
                    await bot.send_video(user_id, media_id, caption=caption)
            
            sent_count += 1
            # Делаем небольшую паузу, чтобы не превысить ограничения API Telegram
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
            failed_count += 1
    
    logger.info(f"Рассылка завершена: отправлено {sent_count}, ошибок {failed_count}")
    return sent_count, failed_count

async def scheduled_send(message_id):
    """Функция для выполнения запланированной отправки"""
    logger.info(f"Выполнение запланированной рассылки #{message_id}")
    
    messages = get_scheduled_messages()
    target_message = None
    
    for msg in messages:
        if msg[0] == message_id:
            target_message = msg
            break
    
    if not target_message:
        logger.error(f"Сообщение #{message_id} не найдено в запланированных")
        return
    
    msg_id, msg_type, msg_content, media_id, caption, _ = target_message
    
    try:
        sent, failed = await send_message_to_subscribers(msg_type, msg_content, media_id, caption)
        update_message_status(message_id, 'sent')
        logger.info(f"Запланированная рассылка #{message_id} выполнена: {sent} отправлено, {failed} ошибок")
    except Exception as e:
        update_message_status(message_id, 'failed')
        logger.error(f"Ошибка при выполнении запланированной рассылки #{message_id}: {e}")

# Обработчики команд
@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    welcome_text = f"Привет, {hbold(first_name)}! 👋\n\n"
    welcome_text += "Я бот для рассылки важных сообщений.\n\n"
    welcome_text += "Доступные команды:\n"
    welcome_text += "/subscribe - подписаться на рассылку\n"
    welcome_text += "/unsubscribe - отписаться от рассылки\n"
    welcome_text += "/status - узнать статус подписки"
    
    if is_admin(user_id):
        welcome_text += f"\n\n{hbold('Вы являетесь администратором!')} Дополнительные команды:\n"
        welcome_text += "/send_message - отправить сообщение всем подписчикам\n"
        welcome_text += "/stats - статистика по подписчикам"
    
    await message.answer(welcome_text)

@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    """Обработчик команды /subscribe"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    if is_subscribed(user_id):
        await message.answer("Вы уже подписаны на рассылку! 😊")
        return
    
    add_subscriber(user_id, username, first_name, last_name)
    await message.answer("Вы успешно подписались на рассылку! 🎉\nТеперь вы будете получать важные сообщения.")

@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message):
    """Обработчик команды /unsubscribe"""
    user_id = message.from_user.id
    
    if not is_subscribed(user_id):
        await message.answer("Вы не были подписаны на рассылку. 🤔")
        return
    
    remove_subscriber(user_id)
    await message.answer("Вы успешно отписались от рассылки. 👋\nНадеемся увидеть вас снова!")

@router.message(Command("status"))
async def cmd_status(message: Message):
    """Обработчик команды /status"""
    user_id = message.from_user.id
    
    if is_subscribed(user_id):
        await message.answer("Вы подписаны на рассылку! 👍")
    else:
        await message.answer("Вы не подписаны на рассылку. Используйте /subscribe чтобы подписаться.")

@router.message(Command("send_message"))
async def cmd_send_message(message: Message):
    """Обработчик команды /send_message"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    kb = InlineKeyboardBuilder()
    kb.button(text="Отправить сейчас", callback_data="send_now")
    kb.button(text="Запланировать", callback_data="schedule")
    kb.adjust(2)
    
    await message.answer(
        "Выберите режим отправки сообщения:",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data.in_(["send_now", "schedule"]))
async def process_send_mode(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора режима отправки"""
    await callback.answer()
    
    send_mode = callback.data
    await state.update_data(send_mode=send_mode)
    
    if send_mode == 'send_now':
        await callback.message.answer(
            "Отправьте сообщение, которое нужно разослать подписчикам.\n\n"
            "Вы можете отправить текст, фото или видео.",
        )
    else:  # schedule
        await callback.message.answer(
            "Отправьте сообщение, которое нужно запланировать для рассылки.\n\n"
            "Вы можете отправить текст, фото или видео.",
        )
    
    await state.set_state(SendMessageStates.waiting_for_message)

@router.message(SendMessageStates.waiting_for_message)
async def process_message_for_sending(message: Message, state: FSMContext):
    """Обработчик получения сообщения для рассылки"""
    user_data = await state.get_data()
    send_mode = user_data.get('send_mode')
    
    if message.text and not message.media_group_id:
        # Обработка текстового сообщения
        await state.update_data(
            message_type='text',
            message_content=message.text,
            media_id=None,
            caption=None
        )
    elif message.photo:
        # Обработка фотографии
        await state.update_data(
            message_type='photo',
            message_content=None,
            media_id=message.photo[-1].file_id,  # Берём последнее (самое качественное) фото
            caption=message.caption or ""
        )
    elif message.video:
        # Обработка видео
        await state.update_data(
            message_type='video',
            message_content=None,
            media_id=message.video.file_id,
            caption=message.caption or ""
        )
    else:
        await message.answer("Пожалуйста, отправьте текст, фото или видео для рассылки.")
        return
    
    if send_mode == 'send_now':
        await send_confirmation(message, state)
    else:  # schedule
        await message.answer(
            "Отлично! Теперь укажите дату и время для рассылки в формате:\n"
            "ДД.ММ.ГГГГ ЧЧ:ММ\n\n"
            "Например: 31.12.2023 15:30"
        )
        await state.set_state(SendMessageStates.waiting_for_schedule_time)

async def send_confirmation(message: Message, state: FSMContext):
    """Отправляет сообщение с подтверждением рассылки"""
    user_data = await state.get_data()
    
    subscribers_count = count_subscribers()
    
    confirmation_text = f"📬 {hbold('Подтверждение рассылки')}\n\n"
    confirmation_text += f"Сообщение будет отправлено {hbold(str(subscribers_count))} подписчикам.\n\n"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data="confirm_send")
    kb.button(text="❌ Отменить", callback_data="cancel_send")
    kb.adjust(2)
    
    await message.answer(confirmation_text, reply_markup=kb.as_markup())
    await state.set_state(SendMessageStates.confirm_sending)

@router.message(SendMessageStates.waiting_for_schedule_time)
async def process_schedule_time(message: Message, state: FSMContext):
    """Обработчик получения времени для планирования рассылки"""
    try:
        # Парсим дату и время
        schedule_time = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
        
        # Проверяем, что дата не в прошлом
        if schedule_time <= datetime.now():
            await message.answer("Ошибка: нельзя запланировать рассылку на прошедшее время.\n"
                               "Пожалуйста, укажите будущую дату и время.")
            return
        
        await state.update_data(schedule_time=schedule_time)
        
        # Формируем сообщение с информацией о планировании
        user_data = await state.get_data()
        message_type = user_data.get('message_type')
        scheduled_text = f"📅 {hbold('Планирование рассылки')}\n\n"
        scheduled_text += f"Тип сообщения: {message_type}\n"
        scheduled_text += f"Запланировано на: {schedule_time.strftime('%d.%m.%Y %H:%M')}\n"
        scheduled_text += f"Получатели: {count_subscribers()} подписчиков\n\n"
        
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Подтвердить", callback_data="confirm_schedule")
        kb.button(text="❌ Отменить", callback_data="cancel_send")
        kb.adjust(2)
        
        await message.answer(scheduled_text, reply_markup=kb.as_markup())
        await state.set_state(SendMessageStates.confirm_sending)
        
    except ValueError:
        await message.answer("Ошибка: неверный формат даты и времени.\n"
                           "Пожалуйста, используйте формат ДД.ММ.ГГГГ ЧЧ:ММ\n"
                           "Например: 31.12.2023 15:30")

@router.callback_query(F.data.in_(["confirm_send", "cancel_send", "confirm_schedule"]), SendMessageStates.confirm_sending)
async def process_sending_confirmation(callback: CallbackQuery, state: FSMContext):
    """Обработчик подтверждения отправки сообщения"""
    await callback.answer()
    
    if callback.data == 'cancel_send':
        await callback.message.answer("Рассылка отменена.")
        await state.clear()
        return
    
    user_data = await state.get_data()
    message_type = user_data.get('message_type')
    message_content = user_data.get('message_content')
    media_id = user_data.get('media_id')
    caption = user_data.get('caption')
    send_mode = user_data.get('send_mode')
    
    if callback.data == 'confirm_send':
        # Отправляем сразу
        await callback.message.answer("Начинаю рассылку...")
        
        sent, failed = await send_message_to_subscribers(message_type, message_content, media_id, caption)
        
        await callback.message.answer(
            f"✅ {hbold('Рассылка завершена!')}\n\n"
            f"Отправлено: {sent}\n"
            f"Ошибок: {failed}"
        )
    
    elif callback.data == 'confirm_schedule':
        # Планируем отправку
        schedule_time = user_data.get('schedule_time')
        
        # Добавляем в базу данных
        message_id = add_scheduled_message(
            message_type, 
            message_content, 
            media_id, 
            caption, 
            schedule_time.strftime("%Y-%m-%d %H:%M:%S"),
            callback.from_user.id
        )
        
        # Планируем задачу
        scheduler.add_job(
            scheduled_send,
            trigger=DateTrigger(run_date=schedule_time),
            args=[message_id],
            id=f"msg_{message_id}"
        )
        
        await callback.message.answer(
            f"✅ {hbold('Рассылка запланирована!')}\n\n"
            f"ID рассылки: {message_id}\n"
            f"Время отправки: {schedule_time.strftime('%d.%m.%Y %H:%M')}\n"
            f"Получатели: {count_subscribers()} подписчиков"
        )
    
    await state.clear()

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Обработчик команды /stats"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    subscribers_count = count_subscribers()
    
    stats_text = f"📊 {hbold('Статистика бота')}\n\n"
    stats_text += f"Всего подписчиков: {subscribers_count}\n"
    
    # Получаем запланированные сообщения
    scheduled = get_scheduled_messages()
    stats_text += f"\nЗапланированные рассылки: {len(scheduled)}\n"
    
    if scheduled:
        stats_text += f"\n📅 {hbold('Ближайшие рассылки:')}\n"
        for i, msg in enumerate(scheduled[:5]):  # Показываем только 5 ближайших
            msg_id, msg_type, _, _, _, scheduled_time = msg
            scheduled_dt = datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M:%S")
            stats_text += f"{i+1}. ID: {msg_id}, Тип: {msg_type}, Время: {scheduled_dt.strftime('%d.%m.%Y %H:%M')}\n"
    
    await message.answer(stats_text)

# Запуск бота
async def on_startup():
    """Действия при запуске бота"""
    init_db()
    
    # Восстанавливаем запланированные задачи из базы данных
    scheduled_messages = get_scheduled_messages()
    for msg in scheduled_messages:
        msg_id, _, _, _, _, scheduled_time = msg
        scheduled_dt = datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M:%S")
        
        # Если время еще не наступило
        if scheduled_dt > datetime.now():
            scheduler.add_job(
                scheduled_send,
                trigger=DateTrigger(run_date=scheduled_dt),
                args=[msg_id],
                id=f"msg_{msg_id}"
            )
            logger.info(f"Восстановлена запланированная рассылка #{msg_id} на {scheduled_time}")
    
    # Запускаем планировщик
    scheduler.start()
    logger.info("Планировщик запущен")
    
    # Логируем информацию о запуске бота
    logger.info("Бот запущен и готов к работе!")

async def on_shutdown():
    """Действия при остановке бота"""
    # Останавливаем планировщик
    scheduler.shutdown()
    logger.info("Планировщик остановлен")
    
    # Закрываем соединения
    logger.info("Бот остановлен")

async def main():
    # Запускаем процесс поллинга новых апдейтов
    await on_startup()
    try:
        await dp.start_polling(bot)
    finally:
        await on_shutdown()

if __name__ == '__main__':
    asyncio.run(main())