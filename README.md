### Billing Service
 To start the project you need to configure .env.prod files in next directories:
 1. admin_panel/config/settings
 
 
    DATABASE=postgres
    DB_HOST=billing_db
    DB_PORT=5432
    DB_NAME=billing
    DB_USER=my_user
    DB_PASSWORD=my_password
    SECRET_KEY=my_secret_key
 
 2. db
 
 
    POSTGRES_USER=my_user
    POSTGRES_PASSWORD=my_pass
    POSTGRES_DB=billing
    
 3. scheduler
    
    
    DB_HOST=billing_db
    DB_PORT=5432
 
 docker-compose up -d
 TODO: BILLING API TO COMPOSE

    