-- ============================================
  -- RBAC 分表初始化数据
  -- 包含两类权限资源: API、MENU
  -- ============================================

  -- ----------------------------
  -- 1. 菜单类型权限 (MENU)
  -- ----------------------------
  INSERT INTO menu_permissions (id, name, parent_id, path, component, sort_order, created_at, updated_at) VALUES
(0, '首页', NULL, '/', '/',1, NOW(), NOW()),
(1, '智能内容检测', NULL, '/detection', '/detection', 2, NOW(), NOW()),
(2, '多模态水印', NULL, '/watermark', '/watermark', 3, NOW(), NOW()),
(3, '标签管理', NULL, '/labels', '/labels', 4, NOW(), NOW()),
(4, '用户管理', NULL, '/users', '/users', 5, NOW(), NOW()),
(5, '角色管理', NULL, '/roles', '/roles', 6, NOW(), NOW()),
(100, '智能文本检测', 1, '/detection/text', '/detection/text', 100, NOW(), NOW()),
(10000, '文本审核', 100, '/detection/text/online', '/detection/text/online', 101, NOW(), NOW()),
(10001, '文本历史检测记录', 100, '/detection/text/history', '/detection/text/history', 102, NOW(), NOW()),
(10002, '敏感词配置', 100, '/detection/text/blacklist', '/detection/text/blacklist', 103, NOW(), NOW()),
(10003, '文本策略配置', 100,'/detection/text/policy', '/detection/text/policy', 104, NOW(), NOW()),
(101, '智能图片检测', 1, '/detection/image', '/detection/image', 105, NOW(), NOW()),
(10100, '图片审核', 101, '/detection/image/online', '/detection/image/online', 106, NOW(), NOW()),
(10101, '图片历史检测记录', 101, '/detection/image/history', '/detection/image/history', 107, NOW(), NOW()),
(10102, '图片策略配置', 101,'/detection/image/policy', '/detection/image/policy', 108, NOW(), NOW()),
(102, '智能音频检测', 1, '/detection/audio', '/detection/audio', 109, NOW(), NOW()),
(10200, '音频审核', 102, '/detection/audio/online', '/detection/audio/online', 110, NOW(), NOW()),
(10201, '音频历史检测记录', 102, '/detection/audio/history', '/detection/audio/history', 111, NOW(), NOW()),
(10202, '音频策略配置', 102,'/detection/audio/policy', '/detection/audio/policy', 112, NOW(), NOW()),
(103, '智能视频检测', 1, '/detection/video', '/detection/video', 113, NOW(), NOW()),
(10300, '视频审核', 102, '/detection/video/online', '/detection/video/online', 114, NOW(), NOW()),
(10301, '视频历史检测记录', 102, '/detection/video/history', '/detection/video/history', 115, NOW(), NOW()),
(10302, '视频策略配置', 102,'/detection/video/policy', '/detection/video/policy', 116, NOW(), NOW());

  -- ----------------------------
  -- 3. API类型权限 (API)
  -- API权限用于后端接口鉴权，通常与Casbin策略配合使用
  -- ----------------------------
INSERT INTO api_permissions (id, name, group_name, api_path, method, created_at, updated_at) VALUES
--
(1001, '获取全局接口权限', '权限管理', '/api/v1/permissions/api', 'GET', NOW(), NOW()),
(1002, '获取全局菜单权限', '权限管理', '/api/v1/permissions/menus', 'GET', NOW(), NOW()),
(1003, '获取全局数据权限', '权限管理', '/api/v1/permissions/data', 'GET', NOW(), NOW()),
(1004, '新增菜单权限', '权限管理', '/api/v1/permissions/menus', 'POST', NOW(), NOW()),
(1005, '修改菜单权限', '权限管理', '/api/v1/permissions/{menu_id}', 'PUT', NOW(), NOW()),
(1006, '删除菜单权限', '权限管理', '/api/v1/permissions/{menu_id}', 'DELETE', NOW(), NOW()),
--
(2001, '获取角色列表', '角色管理', '/api/v1/roles', 'GET', NOW(), NOW()),
(2002, '创建角色', '角色管理', '/api/v1/roles', 'POST', NOW(), NOW()),
(2003, '修改角色信息', '角色管理', '/api/v1/roles/{role_id}', 'PUT', NOW(), NOW()),
(2004, '保存角色接口权限', '角色管理', '/api/v1/roles/{role_id}/api-permissions', 'PUT', NOW(), NOW()),
(2005, '保存角色数据权限', '角色管理', '/api/v1/roles/{role_id}/data-permissions', 'PUT', NOW(), NOW()),
(2006, '获取角色接口权限列表', '角色管理', '/api/v1/roles/{role_id}/api-permissions', 'GET', NOW(), NOW()),
(2007, '获取角色数据权限列表', '角色管理', '/api/v1/roles/{role_id}/data-permissions', 'GET', NOW(), NOW()),
(2008, '获取角色菜单权限', '角色管理', '/api/v1/roles/{role_id}/menus', 'GET', NOW(), NOW()),
(2009, '保存角色菜单权限', '角色管理', '/api/v1/roles/{role_id}/menus', 'PUT', NOW(), NOW()),
--
(3001, '获取用户列表', '用户管理', '/api/v1/users', 'GET', NOW(), NOW()),
(3002, '创建用户', '用户管理', '/api/v1/users', 'POST', NOW(), NOW()),
(3003, '获取当前登录用户信息', '用户管理', '/api/v1/users/me', 'GET', NOW(), NOW()),
(3004, '获取用户页面菜单', '用户管理', '/api/v1/users/me/menus', 'GET', NOW(), NOW()),
(3005, '修改用户信息', '用户管理', '/api/v1/users/{user_id}', 'PUT', NOW(), NOW()),
(3006, '用户分配角色', '用户管理', '/api/v1/users/{user_id}/roles', 'POST', NOW(), NOW()),
(3007, '获取用户详情', '用户管理', '/api/v1/users/{user_id}', 'GET', NOW(), NOW()),
--
(4001, '获取标签树', '标签管理', '/api/v1/labels/tree', 'GET', NOW(), NOW()),
(4002, '获取标签列表', '标签管理', '/api/v1/labels', 'GET', NOW(), NOW()),
(4003, '创建标签', '标签管理', '/api/v1/labels', 'POST', NOW(), NOW()),
(4004, '更新标签', '标签管理', '/api/v1/labels/{id}', 'PUT', NOW(), NOW()),
(4006, '启停用标签', '标签管理', '/api/v1/labels/{id}/enable', 'PUT', NOW(), NOW()),
(4007, '删除标签', '标签管理', '/api/v1/labels/{id}', 'DELETE', NOW(), NOW()),
--
(5001, '创建应用', '应用场景管理', '/api/v1/applications', 'POST', NOW(), NOW()),
(5002, '查询应用列表', '应用场景管理', '/api/v1/applications', 'GET', NOW(), NOW()),
(5003, '获取应用详情', '应用场景管理', '/api/v1/applications/{application_id}', 'GET', NOW(), NOW()),
(5004, '更新应用', '应用场景管理', '/api/v1/applications/{application_id}', 'PUT', NOW(), NOW()),
(5005, '删除应用', '应用场景管理', '/api/v1/applications/{application_id}', 'DELETE', NOW(), NOW()),
(5006, '创建场景', '应用场景管理', '/api/v1/scenes', 'POST', NOW(), NOW()),
(5007, '查询场景列表', '应用场景管理', '/api/v1/scenes', 'GET', NOW(), NOW()),
(5008, '获取场景详情', '应用场景管理', '/api/v1/scenes/{scene_id}', 'GET', NOW(), NOW()),
(5009, '更新场景', '应用场景管理', '/api/v1/scenes/{scene_id}', 'PUT', NOW(), NOW()),
(5010, '删除场景', '应用场景管理', '/api/v1/scenes/{scene_id}', 'DELETE', NOW(), NOW()),
--
(6001, '创建敏感词', '敏感词管理', '/api/v1/sensitive-words', 'POST', NOW(), NOW()),
(6002, '查询敏感词列表', '敏感词管理', '/api/v1/sensitive-words', 'GET', NOW(), NOW()),
(6003, '查询敏感词详情', '敏感词管理', '/api/v1/sensitive-words/{sensitive_word_id}', 'GET', NOW(), NOW()),
(6004, '敏感词更新', '敏感词管理', '/api/v1/sensitive-words/{sensitive_word_id}', 'PUT', NOW(), NOW()),
(6005, '修改敏感词状态', '敏感词管理', '/api/v1/sensitive-words/{sensitive_word_id}/status', 'PUT', NOW(), NOW()),
--
(7001, '创建策略', '策略管理', '/api/v1/policies', 'POST', NOW(), NOW()),
(7002, '查询策略列表', '策略管理', '/api/v1/policies', 'GET', NOW(), NOW()),
(7003, '获取策略详情', '策略管理', '/api/v1/policies/{policy_id}', 'GET', NOW(), NOW()),
(7004, '更新策略', '策略管理', '/api/v1/policies/{policy_id}', 'PUT', NOW(), NOW()),
(7005, '删除策略', '策略管理', '/api/v1/policies/{policy_id}', 'DELETE', NOW(), NOW()),
(7006, '发布策略', '策略管理', '/api/v1/policies/{policy_id}/publish', 'POST', NOW(), NOW()),
(7007, '下线策略', '策略管理', '/api/v1/policies/{policy_id}/unpublish', 'POST', NOW(), NOW()),
(7008, '启用或停用策略', '策略管理', '/api/v1/policies/{policy_id}/toggle', 'POST', NOW(), NOW()),
--
(8001, '上传媒体文件', '文件上传', '/api/v1/files/upload', 'POST', NOW(), NOW()),
--
(9001, '敏感词在线测试', '在线检测', '/api/v1/online-test/sensitive-word', 'POST', NOW(), NOW()),
(9002, '文本在线测试', '在线检测', '/api/v1/online-test/text', 'POST', NOW(), NOW()),
(9003, '音频在线测试', '在线检测', '/api/v1/online-test/audio', 'POST', NOW(), NOW()),
(9004, '图像在线测试', '在线检测', '/api/v1/online-test/image', 'POST', NOW(), NOW()),
(9005, '视频在线测试', '在线检测', '/api/v1/online-test/video', 'POST', NOW(), NOW()),
(9006, '知识库代答在线测试', '在线检测', '/api/v1/online-test/knowledge', 'POST', NOW(), NOW()),
--
(10001, '下载离线审核任务CSV模板', '离线批量审核', '/api/v1/offline-audit/templates/{job_type}', 'GET', NOW(), NOW()),
(10002, '创建离线审核任务', '离线批量审核', '/api/v1/offline-audit/{job_type}/jobs', 'POST', NOW(), NOW()),
(10003, '查询离线审核任务列表', '离线批量审核', '/api/v1/offline-audit/jobs', 'GET', NOW(), NOW()),
(10004, '删除离线审核任务', '离线批量审核', '/api/v1/offline-audit/jobs', 'DELETE', NOW(), NOW()),
--
(11001, '分页查询审核记录', '历史审核记录', '/api/v1/audit-records', 'GET', NOW(), NOW()),
(11002, '查询审核记录详情', '历史审核记录', '/api/v1/audit-records/{request_id}', 'GET', NOW(), NOW()),
(11003, '删除审核记录', '历史审核记录', '/api/v1/audit-records', 'DELETE', NOW(), NOW());

-- 超级管理员赋予全部数据权限
INSERT INTO role_data_scope_rules (id, role_id, resource_type, view_scope, edit_scope, is_active) VALUES
(1, 1, '__all__', 'ALL', 'ALL', 1);