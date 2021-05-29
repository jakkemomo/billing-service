create schema if not exists data;
alter database billing_test set search_path to data;
create table if not exists data.payment_methods (
               id uuid primary key,
               external_id varchar(50),
               user_id uuid not null,
               payment_system varchar(50) not null,
               type varchar(50) not null,
               is_default boolean default FALSE not null,
               data json not null,
               created timestamptz default now(),
               modified timestamptz default now());
create table if not exists data.products (
               id uuid primary key,
               name varchar(255) not null,
               description text,
               role_id uuid not null,
               price decimal not null,
               currency_code varchar(3) not null,
               period integer not null,
               active boolean default FALSE not null,
               created timestamptz default now(),
               modified timestamptz default now());
create type data.subscription_state as enum ('active', 'pre_active', 'inactive', 'cancelled', 'to_deactivate');
create table if not exists data.subscriptions (
               id uuid primary key,
               product_id uuid references data.products on update cascade on delete restrict ,
               user_id uuid not null,
               start_date date not null,
               end_date date not null,
               state data.subscription_state default 'inactive',
               created timestamptz default now(),
               modified timestamptz default now());
create type data.order_state as enum ('draft', 'processing', 'paid', 'error');
create table if not exists data.orders (
              id uuid primary key,
              external_id varchar(50),
              product_id uuid references data.products on update cascade on delete restrict,
              subscription_id uuid references data.subscriptions on update cascade on delete restrict,
              user_id uuid not null,
              payment_system varchar(50) not null,
              payment_method_id uuid references data.payment_methods on update cascade on delete restrict,
              payment_amount decimal not null,
              payment_currency_code varchar(3) not null,
              user_email varchar(35) not null,
              state data.order_state default 'draft',
              is_automatic boolean default FALSE not null,
              is_refund boolean default FALSE not null,
              src_order_id uuid references data.orders on update cascade on delete restrict,
              created timestamptz default now(),
              modified timestamptz default now());
