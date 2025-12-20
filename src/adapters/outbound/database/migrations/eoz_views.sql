-- SQL запросы для создания View для сверки задач ЕОЗ
-- Эти запросы должны быть добавлены в миграцию Alembic

-- =====================================================
-- 1. View для задач (eoz_tasks_view)
-- =====================================================

CREATE OR REPLACE VIEW eoz_tasks_view AS
SELECT
    tt.id,
    tt.name,
    tt.uri,
    tt.short_desc AS short_description,
    CASE
        WHEN tt.status = 'NEW' AND tt.decision = 'NOT_DECIDED' THEN 'CREATED'
        WHEN tt.status = 'COMPLETED' AND tt.decision != 'NOT_DECIDED' THEN 'CLOSED'
        WHEN tt.status = 'CANCELLED' THEN 'DELETED'
    END AS status,
    'Акты и Накладные' AS source_name,
    tt.created_at,
    tt.deadline_at AS deadline,
    tt.updated_at,
    tt.done_at AS closed_at
FROM task_tasks tt;

COMMENT ON VIEW eoz_tasks_view IS 'View для предоставления данных по задачам для автоматической сверки с ЕОЗ';

-- =====================================================
-- 2. View для участников задач (eoz_task_members_view)
-- =====================================================

CREATE OR REPLACE VIEW eoz_task_members_view AS
-- Reporter (AUTHOR) - всегда пользователь
SELECT
    tt.id AS task_id,
    'AUTHOR' AS member_role,
    u_reporter.hr_id AS id,
    'USER' AS type
FROM task_tasks tt
INNER JOIN user_users u_reporter ON tt.reporter_id = u_reporter.id
WHERE u_reporter.hr_id IS NOT NULL

UNION ALL

-- Executor (EXECUTOR) - пользователь, если executor_id не NULL
SELECT
    tt.id AS task_id,
    'EXECUTOR' AS member_role,
    u_executor.hr_id AS id,
    'USER' AS type
FROM task_tasks tt
INNER JOIN user_users u_executor ON tt.executor_id = u_executor.id
WHERE tt.executor_id IS NOT NULL
    AND u_executor.hr_id IS NOT NULL

UNION ALL

-- Executor (EXECUTOR) - роль, если executor_id NULL
-- Берем первую роль, связанную с permission (через MIN для детерминированности)
SELECT
    tt.id AS task_id,
    'EXECUTOR' AS member_role,
    (
        SELECT ur_sub.id
        FROM user_role_permissions_association urpa_sub
        INNER JOIN user_roles ur_sub ON urpa_sub.role_id = ur_sub.id
        WHERE urpa_sub.permission_id = tt.permission_id
        ORDER BY ur_sub.id
        LIMIT 1
    ) AS id,
    'ROLE' AS type
FROM task_tasks tt
WHERE tt.executor_id IS NULL
    AND tt.permission_id IS NOT NULL
    AND EXISTS (
        SELECT 1
        FROM user_role_permissions_association urpa_check
        WHERE urpa_check.permission_id = tt.permission_id
    );

COMMENT ON VIEW eoz_task_members_view IS 'View для предоставления данных по участникам задач для автоматической сверки с ЕОЗ';

-- =====================================================
-- 3. SQL запросы для удаления View (для downgrade)
-- =====================================================

-- DROP VIEW IF EXISTS eoz_task_members_view;
-- DROP VIEW IF EXISTS eoz_tasks_view;
