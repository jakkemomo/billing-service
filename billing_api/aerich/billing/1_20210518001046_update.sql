-- upgrade --
ALTER TABLE "orders" ADD "is_refund" BOOL NOT NULL  DEFAULT False;
ALTER TABLE "orders" ADD "src_order_id" UUID;
ALTER TABLE "orders" ADD CONSTRAINT "fk_orders_orders_006331c4" FOREIGN KEY ("src_order_id") REFERENCES "orders" ("id") ON DELETE RESTRICT;
-- downgrade --
ALTER TABLE "orders" DROP CONSTRAINT "fk_orders_orders_006331c4";
ALTER TABLE "orders" DROP COLUMN "is_refund";
ALTER TABLE "orders" DROP COLUMN "src_order_id";
