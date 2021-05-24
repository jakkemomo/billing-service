-- upgrade --
ALTER TABLE "orders" ADD "user_email" VARCHAR(35) NOT NULL;
-- downgrade --
ALTER TABLE "orders" DROP COLUMN "user_email";
