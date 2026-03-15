-- 为购物车表添加 name 列，用于后端模糊搜索
-- 执行: mysql -u user -p db < migrations/add_shopping_cart_name.sql
-- 新增加购的商品会自动写入 name；已有数据的 name 为 NULL，搜索时不会匹配

ALTER TABLE shopping_cart ADD COLUMN name VARCHAR(200) DEFAULT NULL COMMENT '商品名称，用于搜索';
