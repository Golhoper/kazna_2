"""Модуль для управления схемными объектами SQLAlchemy.

Содержит декларативные определения всех схемных объектов базы данных:
- Sequences (последовательности)
- Indexes (индексы)
- Check constraints (проверочные ограничения)
- Functions (функции)
"""

from sqlalchemy import DDL, Sequence

from adapters.outbound.database.base import SaBase

# =====================================================
# SEQUENCES
# =====================================================

# Старая последовательность для обратной совместимости
act_system_number_seq = Sequence(
    "act_system_number_seq",
    start=1,
    increment=1,
    metadata=SaBase.metadata,
)

# Последовательности для новой системы нумерации документов
# Формат: document_sequence_{document_type_code}_{year}
# Например: document_sequence_01_2025 для актов 2025 года

# =====================================================
# FUNCTIONS
# =====================================================

# Функция для динамического создания последовательностей номеров документов
create_document_sequence_function = DDL(
    """
    CREATE OR REPLACE FUNCTION create_document_sequence_if_not_exists(
        doc_type_code TEXT,
        doc_year INTEGER
    ) RETURNS BIGINT AS $$
    DECLARE
        seq_name TEXT;
        next_val BIGINT;
    BEGIN
        seq_name := 'document_sequence_' || doc_type_code || '_' || doc_year::TEXT;
        -- Проверяем, существует ли последовательность
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.sequences
            WHERE sequence_name = seq_name
            AND sequence_schema = current_schema()
        ) THEN
            -- Создаем последовательность, если её нет
            EXECUTE format('CREATE SEQUENCE %I START 1 INCREMENT 1', seq_name);
        END IF;
        -- Получаем следующее значение
        EXECUTE format('SELECT nextval(%L)', seq_name) INTO next_val;
        RETURN next_val;
    END;
    $$ LANGUAGE plpgsql;
    """,
)

# ПРИМЕЧАНИЕ: Функция создается через миграцию Alembic, а не через SQLAlchemy метаданные
# См. миграцию: 0050_2025-09-19-15-39-29.py

# Пример других полезных схемных объектов:

# =====================================================
# INDEXES (если нужны составные индексы)
# =====================================================
# from sqlalchemy import Index
#
# acts_status_date_idx = Index(
#     "ix_acts_status_planning_date",
#     "status", "planning_date",
#     postgresql_where=text("deleted_at IS NULL")
# )

# =====================================================
# CHECK CONSTRAINTS (если нужны)
# =====================================================
# from sqlalchemy import CheckConstraint, text
#
# positive_sum_constraint = CheckConstraint(
#     "total_sum >= 0",
#     name="ck_acts_positive_total_sum"
# )

# =====================================================
# FUNCTIONS (если нужны)
# =====================================================
# from sqlalchemy import DDL, event
#
# # Пример создания функции через DDL
# create_system_number_function = DDL("""
#     CREATE OR REPLACE FUNCTION generate_act_system_number()
#     RETURNS TEXT AS $$
#     BEGIN
#         RETURN LPAD(nextval('act_system_number_seq')::TEXT, 10, '0');
#     END;
#     $$ LANGUAGE plpgsql;
# """)
#
# # Привязка к метаданным
# event.listen(SaBase.metadata, "after_create", create_system_number_function)
