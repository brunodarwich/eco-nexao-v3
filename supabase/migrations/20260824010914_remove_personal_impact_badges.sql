-- ADR 0009 removes personal ecological scoring and badges from the product.
-- Trips and actor visits remain intact as the user's travel history.
DROP TABLE IF EXISTS app_private.user_badges;
