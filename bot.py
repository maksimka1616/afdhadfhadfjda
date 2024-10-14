import telebot
import sqlite3
import re
import datetime
import schedule
import time

bot = telebot.TeleBot('8146601076:AAFzZ7uFVRG64b3NnLQWAhRyvpk08pF2J38')  # Замените на ваш токен

def create_table():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_data (
            id INTEGER PRIMARY KEY,
            total_rating INTEGER DEFAULT 0,
            total_coins INTEGER DEFAULT 0,
            day_rating INTEGER DEFAULT 0,
            day_coins INTEGER DEFAULT 0,
            week_rating INTEGER DEFAULT 0,
            week_coins INTEGER DEFAULT 0,
            month_rating INTEGER DEFAULT 0,
            month_coins INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

create_table()


def get_user_data(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            total_rating, total_coins, 
            day_rating, day_coins, 
            week_rating, week_coins, 
            month_rating, month_coins 
        FROM user_data WHERE id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'total_rating': row[0], 'total_coins': row[1],
            'day_rating': row[2], 'day_coins': row[3],
            'week_rating': row[4], 'week_coins': row[5],
            'month_rating': row[6], 'month_coins': row[7]
        }
    else:
        return {
            'total_rating': 0, 'total_coins': 0,
            'day_rating': 0, 'day_coins': 0,
            'week_rating': 0, 'week_coins': 0,
            'month_rating': 0, 'month_coins': 0
        }

def update_user_data(user_id, rating, coins):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO user_data (id) VALUES (?)", (user_id,))
    cursor.execute("""
        UPDATE user_data SET 
            total_rating = total_rating + ?, 
            total_coins = total_coins + ?,
            day_rating = day_rating + ?, 
            day_coins = day_coins + ?,
            week_rating = week_rating + ?, 
            week_coins = week_coins + ?,
            month_rating = month_rating + ?, 
            month_coins = month_coins + ?
        WHERE id = ?
    """, (rating, coins, rating, coins, rating, coins, rating, coins, user_id))
    conn.commit()
    conn.close()

def send_daily_report():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, day_rating, day_coins FROM user_data")
    users = cursor.fetchall()
    for user_id, day_rating, day_coins in users:
        try:
            bot.send_message(1971188182, f"Отчет за сегодня для пользователя {user_id}:\nРейтинг: {day_rating}\nМонеты: {day_coins}")
            cursor.execute("UPDATE user_data SET day_rating = 0, day_coins = 0 WHERE id = ?", (user_id,))
        except telebot.apihelper.ApiException as e:
            print(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
    conn.commit()
    conn.close()

def send_weekly_report():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, week_rating, week_coins FROM user_data")
    users = cursor.fetchall()
    for user_id, week_rating, week_coins in users:
        try:
            bot.send_message(1971188182, f"Отчет за неделю для пользователя {user_id}:\nРейтинг: {week_rating}\nМонеты: {week_coins}")
            cursor.execute("UPDATE user_data SET week_rating = 0, week_coins = 0 WHERE id = ?", (user_id,))
        except telebot.apihelper.ApiException as e:
            print(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
    conn.commit()
    conn.close()

schedule.every().day.at("00:00").do(send_daily_report)
schedule.every().monday.at("00:00""").do(send_weekly_report)

@bot.message_handler(commands=['info'])
def handle_info(message):
    user_data = get_user_data(message.from_user.id)
    report = f"""Всего заработано:
1д: {user_data['day_rating']}р|{user_data['day_coins']}м
1н: {user_data['week_rating']}р|{user_data['week_coins']}м
1м: {user_data['month_rating']}р|{user_data['month_coins']}м
Все время: {user_data['total_rating']}р|{user_data['total_coins']}м"""
    bot.reply_to(message, report)

@bot.message_handler(func=lambda message: message.text is not None and not message.text.startswith('/'))
def handle_message(message):
    text = message.text
    match = re.search(r"💫 Империя получила:\s*(\d+)\s*рейтинга\s*и\s*(\d+)\s*золотых\s*монеток", text)
    if match:
        try:
            rating = int(match.group(1))
            coins = int(match.group(2))
            update_user_data(message.from_user.id, rating, coins)
            bot.pin_chat_message(message.chat.id, message.message_id)
            bot.reply_to(message, "Сообщение закреплено!")
            bot.send_message(1971188182, f"💫 Империя получила: {rating} рейтинга и {coins} золотых монеток") # замените 1971188182 на ваш ID
        except (ValueError, IndexError, AttributeError):
            bot.reply_to(message, "Не могу разобрать сообщение об экспедиции. Проверьте формат.")
        except telebot.apihelper.ApiException as e:
            if e.error_code == 400:
                bot.reply_to(message, "Не могу закрепить сообщение. Возможно, у меня нет прав.")
            else:
                bot.reply_to(message, f"Ошибка при закреплении сообщения: {e}")
    elif "поздравляю, ваша империя перешла в стадию «сбор на экспедицию» 🧳" in text.lower():
        try:
            bot.pin_chat_message(message.chat.id, message.message_id)
            bot.reply_to(message, "Сообщение закреплено!")
        except telebot.apihelper.ApiException as e:
            if e.error_code == 400:
                bot.reply_to(message, "Не могу закрепить сообщение. Возможно, у меня нет прав.")
            else:
                bot.reply_to(message, f"Ошибка при закреплении сообщения: {e}")

bot.polling()

while True:
    schedule.run_pending()
    time.sleep(1)