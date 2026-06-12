import sqlite3

import aiosqlite

DB_PATH = "lottery.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # 1. Создаем таблицу с НОВЫМ столбцом winner_user_id
        await db.execute('''
            CREATE TABLE IF NOT EXISTS lotteries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prize TEXT,
                ticket_price INTEGER,
                total_tickets INTEGER,
                sold_tickets INTEGER DEFAULT 0,
                channel_id INTEGER,
                status TEXT DEFAULT 'active',
                winner_user_id INTEGER DEFAULT NULL
            )
        ''')

        # 2. Миграция: пытаемся добавить столбец, если таблица была создана ранее без него
        try:
            await db.execute("ALTER TABLE lotteries ADD COLUMN winner_user_id INTEGER DEFAULT NULL")
        except sqlite3.OperationalError:
            # Если столбец уже существует, SQLite выдаст ошибку. Мы её просто игнорируем.
            pass

            # 3. Таблица билетов
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lottery_id INTEGER,
                user_id INTEGER,
                FOREIGN KEY (lottery_id) REFERENCES lotteries(id)
            )
        ''')
        await db.commit()


# --- CRUD Функции ---

async def create_lottery(prize: str, price: int, total: int, channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO lotteries (prize, ticket_price, total_tickets, channel_id) VALUES (?, ?, ?, ?)",
            (prize, price, total, channel_id)
        )
        await db.commit()


async def get_active_lottery():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM lotteries WHERE status = 'active' LIMIT 1")
        return await cursor.fetchone()


async def buy_ticket(lottery_id: int, user_id: int, quantity: int):
    async with aiosqlite.connect(DB_PATH) as db:
        # Блокировка для предотвращения гонки данных (race condition) на последнем билете
        await db.execute("BEGIN IMMEDIATE")
        cursor = await db.execute("SELECT sold_tickets, total_tickets FROM lotteries WHERE id = ?", (lottery_id,))
        lottery = await cursor.fetchone()

        if lottery[0] + quantity > lottery[1]:
            await db.rollback()
            return False  # Недостаточно билетов

        # Добавляем билеты
        for _ in range(quantity):
            await db.execute("INSERT INTO tickets (lottery_id, user_id) VALUES (?, ?)", (lottery_id, user_id))

        # Обновляем счетчик
        await db.execute(
            "UPDATE lotteries SET sold_tickets = sold_tickets + ? WHERE id = ?",
            (quantity, lottery_id)
        )
        await db.commit()
        return True


async def pick_winner(lottery_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        # Выбираем случайного пользователя, купившего билет в этой лотерее
        cursor = await db.execute(
            "SELECT user_id FROM tickets WHERE lottery_id = ? ORDER BY RANDOM() LIMIT 1",
            (lottery_id,)
        )
        winner = await cursor.fetchone()

        if winner:
            winner_id = winner[0]
            # Помечаем лотерею как завершенную
            await db.execute("UPDATE lotteries SET status = 'completed', winner_user_id = ? WHERE id = ?",
                             (winner_id, lottery_id))
            await db.commit()
            return winner_id
        return None

async def get_all_active_lotteries():
    """Возвращает список всех активных лотерей"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM lotteries WHERE status = 'active'")
        return await cursor.fetchall()

async def get_lottery_by_id(lottery_id: int):
    """Возвращает конкретную лотерею по ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM lotteries WHERE id = ? AND status = 'active'", (lottery_id,))
        return await cursor.fetchone()


async def check_ticket_availability(lottery_id: int, quantity: int) -> bool:
    """
    Проверяет, доступно ли запрошенное количество билетов в лотерее.
    Возвращает True, если билетов хватает, иначе False.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT total_tickets, sold_tickets FROM lotteries WHERE id = ? AND status = 'active'",
            (lottery_id,)
        )
        lottery = await cursor.fetchone()

        if not lottery:
            return False  # Лотерея не найдена или не активна

        total = lottery[0]
        sold = lottery[1]

        return (sold + quantity) <= total