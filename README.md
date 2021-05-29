### Billing Service

The main idea of this project is to implement one business interface to work with multiple payment services when each of them
could have it's own specific interface. For this implementation we used Adapter pattern, realisation could be seen in
the billing_api/src/clients/abstract.py and  billing_api/src/clients/__init__.py



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
    docker exec -it billing-admin-panel python manage.py createsuperuser
