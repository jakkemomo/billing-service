-- upgrade --
ALTER TABLE "orders" ALTER COLUMN "external_id" DROP NOT NULL;
-- downgrade --
ALTER TABLE "orders" ALTER COLUMN "external_id" SET NOT NULL;
