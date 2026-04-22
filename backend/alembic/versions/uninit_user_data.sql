DELETE
FROM `user_roles`
WHERE `user_id` = 1
  AND `role_id` = 1;

DELETE
FROM `users`
WHERE `id` = 1;

DELETE
FROM `roles`
WHERE `id` = 1;
