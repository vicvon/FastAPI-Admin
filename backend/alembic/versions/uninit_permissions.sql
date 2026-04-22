-- 回滚默认权限与授权种子
DELETE
FROM `role_data_scope_rules`
WHERE `role_id` = 1
  AND `resource_type` = '__all__';

DELETE
FROM `role_permissions`
WHERE `role_id` = 1
  AND `permission_id` IN (
                          1001, 1002, 1003, 1004, 1005, 1006,
                          2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
                          3001, 3002, 3003, 3004, 3005,
                          4001, 4002, 4003, 4004, 4005, 4006, 4007
    );

DELETE
FROM `role_menu_permissions`
WHERE `role_id` = 1
  AND `menu_permission_id` IN (1, 2, 3, 4, 5);

DELETE
FROM `api_permissions`
WHERE `id` IN (
               1001, 1002, 1003, 1004, 1005, 1006,
               2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
               3001, 3002, 3003, 3004, 3005,
               4001, 4002, 4003, 4004, 4005, 4006, 4007
    );

DELETE
FROM `menu_permissions`
WHERE `id` IN (1, 2, 3, 4, 5);
