from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from sqlalchemy import (
    BigInteger, String, Text, Integer, Numeric, Boolean, 
    DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


# ==========================================
# 1. ПОЛЬЗОВАТЕЛИ И АДМИНИСТРАТОРЫ
# ==========================================

class User(Base):
    """Покупатели магазина."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Связи
    platform_accounts: Mapped[List["PlatformAccount"]] = relationship(back_populates="user")
    orders: Mapped[List["Order"]] = relationship(back_populates="user")


class PlatformAccount(Base):
    """Аккаунты покупателей в разных платформах (Telegram, VK, MAX)."""
    __tablename__ = "platform_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    platform: Mapped[str] = mapped_column(String(50))  # 'telegram', 'vk', 'max'
    platform_id: Mapped[str] = mapped_column(String(255))  # ID пользователя в конкретной платформе
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Связи
    user: Mapped["User"] = relationship(back_populates="platform_accounts")


class Admin(Base):
    """Администраторы и их роли."""
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    role: Mapped[str] = mapped_column(String(50), default="admin")  # owner, admin, manager, operator
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ==========================================
# 2. КАТАЛОГ ТОВАРОВ
# ==========================================

class Category(Base):
    """Категории и подкатегории товаров."""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Связи
    products: Mapped[List["Product"]] = relationship(back_populates="category")


class Product(Base):
    """Товары."""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), nullable=True)
    
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Numeric(10, 2) гарантирует точность до копеек, как требуют в ТЗ (без float!)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    old_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    
    article: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Артикул
    stock: Mapped[int] = mapped_column(Integer, default=0)  # Остаток
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # В продаже или нет
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)  # Популярность
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Связи
    category: Mapped[Optional["Category"]] = relationship(back_populates="products")
    images: Mapped[List["ProductImage"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    variants: Mapped[List["ProductVariant"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class ProductImage(Base):
    """Фотографии товаров. Храним отдельно для разных платформ."""
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    image_url: Mapped[str] = mapped_column(String(500))  # Ссылка на оригинал или локальный путь
    telegram_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    vk_attachment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Связи
    product: Mapped["Product"] = relationship(back_populates="images")


class ProductVariant(Base):
    """Варианты товаров (размер, цвет и т.д.)."""
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    name: Mapped[str] = mapped_column(String(100))  # Например: "Размер M, Черный"
    article: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)  # Если отличается от базовой
    stock: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Связи
    product: Mapped["Product"] = relationship(back_populates="variants")


# ==========================================
# 3. КОРЗИНА И ЗАКАЗЫ
# ==========================================

class Cart(Base):
    """Корзины пользователей."""
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    items: Mapped[List["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    """Состав корзины."""
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    variant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_variants.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    cart: Mapped["Cart"] = relationship(back_populates="items")


class Order(Base):
    """Заказы."""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    status: Mapped[str] = mapped_column(String(50), default="new")  # new, pending_payment, paid, processing, shipped, completed, cancelled
    
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    delivery_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    
    # Данные покупателя (сохраняем на момент заказа, чтобы не зависеть от изменений профиля)
    customer_name: Mapped[str] = mapped_column(String(255))
    customer_phone: Mapped[str] = mapped_column(String(50))
    delivery_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    track_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    history: Mapped[List["OrderHistory"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Товары в заказе. Сохраняем цену и название на момент покупки."""
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    variant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_variants.id"), nullable=True)
    
    product_name: Mapped[str] = mapped_column(String(255))  # Снимок названия
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))  # Снимок цены
    quantity: Mapped[int] = mapped_column(Integer)

    order: Mapped["Order"] = relationship(back_populates="items")


class OrderHistory(Base):
    """История изменения статусов заказа."""
    __tablename__ = "order_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    status: Mapped[str] = mapped_column(String(50))
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    order: Mapped["Order"] = relationship(back_populates="history")


# ==========================================
# 4. ПЛАТЕЖИ И ДОСТАВКА
# ==========================================

class Payment(Base):
    """Платежи."""
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    provider: Mapped[str] = mapped_column(String(50))  # yookassa, manual, crypto
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(10), default="RUB")
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, success, failed
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # ID в платежной системе
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PaymentEvent(Base):
    """История платёжных уведомлений (вебхуков)."""
    __tablename__ = "payment_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"))
    event_type: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSON)  # Сырой JSON от платежной системы
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DeliveryMethod(Base):
    """Способы доставки."""
    __tablename__ = "delivery_methods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    free_threshold: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)  # Бесплатно от суммы
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


# ==========================================
# 5. НАСТРОЙКИ И МЕНЮ
# ==========================================

class ShopSetting(Base):
    """Глобальные настройки магазина (ключ-значение)."""
    __tablename__ = "shop_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True)  # Например: "shop_name", "welcome_text"
    value: Mapped[str] = mapped_column(Text)  # Значение настройки


class MenuItem(Base):
    """Кнопки главного меню. Позволяет менять меню без кода."""
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100))  # Текст на кнопке
    action_type: Mapped[str] = mapped_column(String(50))  # catalog, cart, contacts, url, page
    action_value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # URL или ID страницы
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)


class NotificationTemplate(Base):
    """Шаблоны уведомлений."""
    __tablename__ = "notification_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_key: Mapped[str] = mapped_column(String(100), unique=True)  # order_created, payment_success
    text: Mapped[str] = mapped_column(Text)