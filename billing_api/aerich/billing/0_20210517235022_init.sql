-- upgrade --
CREATE TABLE IF NOT EXISTS "payment_methods" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created" TIMESTAMPTZ NOT NULL,
    "modified" TIMESTAMPTZ NOT NULL,
    "user_id" UUID NOT NULL,
    "external_id" VARCHAR(50) NOT NULL,
    "payment_system" VARCHAR(50) NOT NULL,
    "type" VARCHAR(50) NOT NULL,
    "is_default" BOOL NOT NULL  DEFAULT False,
    "data" JSONB
);
CREATE TABLE IF NOT EXISTS "products" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created" TIMESTAMPTZ NOT NULL,
    "modified" TIMESTAMPTZ NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "description" TEXT NOT NULL,
    "role_id" UUID NOT NULL,
    "price" DOUBLE PRECISION NOT NULL,
    "currency_code" VARCHAR(3) NOT NULL,
    "period" INT NOT NULL,
    "active" BOOL NOT NULL  DEFAULT False
);
CREATE TABLE IF NOT EXISTS "subscriptions" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created" TIMESTAMPTZ NOT NULL,
    "modified" TIMESTAMPTZ NOT NULL,
    "user_id" UUID NOT NULL,
    "start_date" DATE,
    "end_date" DATE,
    "state" VARCHAR(9) NOT NULL  DEFAULT 'inactive',
    "product_id" UUID NOT NULL REFERENCES "products" ("id") ON DELETE RESTRICT
);
COMMENT ON COLUMN "subscriptions"."state" IS 'ACTIVE: active\nINACTIVE: inactive\nCANCELLED: cancelled';
CREATE TABLE IF NOT EXISTS "orders" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created" TIMESTAMPTZ NOT NULL,
    "modified" TIMESTAMPTZ NOT NULL,
    "external_id" VARCHAR(50) NOT NULL,
    "user_id" UUID NOT NULL,
    "payment_system" VARCHAR(50) NOT NULL,
    "payment_amount" DOUBLE PRECISION NOT NULL,
    "payment_currency_code" VARCHAR(3) NOT NULL,
    "state" VARCHAR(10) NOT NULL  DEFAULT 'draft',
    "is_automatic" BOOL NOT NULL  DEFAULT False,
    "product_id" UUID NOT NULL REFERENCES "products" ("id") ON DELETE RESTRICT,
    "subscription_id" UUID NOT NULL REFERENCES "subscriptions" ("id") ON DELETE RESTRICT,
    "payment_method_id" UUID REFERENCES "payment_methods" ("id") ON DELETE RESTRICT
);
COMMENT ON COLUMN "orders"."state" IS 'DRAFT: draft\nPROCESSING: processing\nPAID: paid\nERROR: error';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSONB NOT NULL
);
