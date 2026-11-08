from sqlalchemy import text
from database.connection import engine

async def update_v1():
    """
    Миграция v1: добавляет новые поля, которых может не быть в старых базах.
    Безопасно: проверяет наличие колонки перед добавлением.
    """
    print("⏳ Применение миграции v1...")
    
    async with engine.begin() as conn:
        # 1. Добавляем timezone в users (если нет)
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='users' AND column_name='timezone'
        """))
        if not result.scalars().first():
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN timezone VARCHAR(50) DEFAULT 'Europe/Moscow'"
            ))
            print("  + Добавлена колонка users.timezone")
        
        # 2. Добавляем old_status в order_history (если нет)
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='order_history' AND column_name='old_status'
        """))
        if not result.scalars().first():
            await conn.execute(text(
                "ALTER TABLE order_history ADD COLUMN old_status VARCHAR(50)"
            ))
            print("  + Добавлена колонка order_history.old_status")
        
        # 3. Добавляем new_status в order_history (если нет)
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='order_history' AND column_name='new_status'
        """))
        if not result.scalars().first():
            await conn.execute(text(
                "ALTER TABLE order_history ADD COLUMN new_status VARCHAR(50)"
            ))
            print("  + Добавлена колонка order_history.new_status")
        
        # 4. Добавляем changed_by в order_history (если нет)
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='order_history' AND column_name='changed_by'
        """))
        if not result.scalars().first():
            await conn.execute(text(
                "ALTER TABLE order_history ADD COLUMN changed_by BIGINT"
            ))
            print("  + Добавлена колонка order_history.changed_by")
        
        # 5. Добавляем requires_address в delivery_methods (если нет)
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='delivery_methods' AND column_name='requires_address'
        """))
        if not result.scalars().first():
            await conn.execute(text(
                "ALTER TABLE delivery_methods ADD COLUMN requires_address BOOLEAN DEFAULT TRUE"
            ))
            print("  + Добавлена колонка delivery_methods.requires_address")
        
        # 6. Добавляем is_free в delivery_methods (если нет)
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='delivery_methods' AND column_name='is_free'
        """))
        if not result.scalars().first():
            await conn.execute(text(
                "ALTER TABLE delivery_methods ADD COLUMN is_free BOOLEAN DEFAULT FALSE"
            ))
            print("  + Добавлена колонка delivery_methods.is_free")
        
        # 7. Меняем тип price в delivery_methods на NUMERIC (если нужно)
        result = await conn.execute(text("""
            SELECT data_type FROM information_schema.columns 
            WHERE table_name='delivery_methods' AND column_name='price'
        """))
        current_type = result.scalars().first()
        if current_type and current_type.lower() in ('character varying', 'varchar', 'text'):
            await conn.execute(text(
                "UPDATE delivery_methods SET price = '0' WHERE price !~ '^[0-9]+(\\.[0-9]+)?$'"
            ))
            await conn.execute(text(
                "ALTER TABLE delivery_methods ALTER COLUMN price TYPE NUMERIC(10, 2) USING price::NUMERIC"
            ))
            await conn.execute(text(
                "ALTER TABLE delivery_methods ALTER COLUMN price SET DEFAULT 0"
            ))
            print("  + Изменен тип delivery_methods.price на NUMERIC")
        
        # 8. Добавляем delivery_method_name в orders (если нет)
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='orders' AND column_name='delivery_method_name'
        """))
        if not result.scalars().first():
            await conn.execute(text(
                "ALTER TABLE orders ADD COLUMN delivery_method_name VARCHAR(255)"
            ))
            print("  + Добавлена колонка orders.delivery_method_name")
    
    print("✅ Миграция v1 применена.")