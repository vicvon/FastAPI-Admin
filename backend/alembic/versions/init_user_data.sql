-- 默认管理员种子快照
-- 由 Alembic revision d0d6403df0d7 执行。
-- 保留本文件作为默认管理员种子 SQL。

INSERT INTO `users` (
    `id`, `username`, `email`, `hashed_password`, `is_active`,
    `full_name`, `created_at`, `updated_at`, `token_version`
) VALUES (
    1, 'admin', 'admin@example.com',
    '$2b$12$Xb.qQOUe3hqTGPS9gmtZS.YWrrTioVBQwhDFwXFJqOy/LDVCkSDWm',
    1, '超级管理员', NOW(), NOW(), 0
);

INSERT INTO `roles` (
    `id`, `name`, `code`, `description`, `is_system`,
    `created_at`, `updated_at`, `parent_role_id`
) VALUES (
    1, '超级管理员', 'role:admin', 'Super administrator',
    1, NOW(), NOW(), NULL
);

INSERT INTO `user_roles` (`user_id`, `role_id`, `created_at`)
VALUES (1, 1, NOW());
