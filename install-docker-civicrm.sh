#!/bin/bash

MYSQL_PASSWORD='mysql_password'
MYSQL_ROOT_PASSWORD='mysql_root_password'
CIVICRM_ADMIN_USER='admin'
CIVICRM_ADMIN_PASS='admin_password'
CIVICRM_ADMIN_API_KEY='49AE35EYiS9OI08PrScZA2MfnbC'
CIVICRM_ADMIN_JSON_FILE='civicrm-admin-data.json'
CIVICRM_VARS_JSON_FILE='civicrm-vars-data.json'

# Clone civicrm-docker and jump into the example civicrm folder.
if [ ! -d civicrm-docker ]; then
    git clone https://github.com/civicrm/civicrm-docker || exit
fi

# Navigate to example civicrm directory.
cd civicrm-docker/example/civicrm || exit

# Create env file with mysql credentials.
cat >.env <<EOL
MYSQL_PASSWORD=${MYSQL_PASSWORD}
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
EOL

# Setup docker container.
docker-compose up --detach || exit

# Wait for mariadb to be ready.
while ! docker-compose logs | grep -q "socket: '/run/mysqld/mysqld.sock'  port: 3306"; do
    sleep 1
done

# Check if the settings file already exists. Otherwise install civicrm.
if ! docker-compose exec app test -f ./private/civicrm.settings.php; then
    docker-compose exec \
        -u www-data \
        -e CIVICRM_ADMIN_USER="$CIVICRM_ADMIN_USER" \
        -e CIVICRM_ADMIN_PASS="$CIVICRM_ADMIN_PASS" \
        app civicrm-docker-install || exit
fi

# Set api key for admin user.
docker-compose exec app \
    cv api4 Contact.update \
    +v "api_key=$CIVICRM_ADMIN_API_KEY" \
    +w 'id = 2' \
    > "$CIVICRM_ADMIN_JSON_FILE" || exit

# Write civicrm vars to json-config-file.
docker-compose exec -u www-data app \
    cv vars:show --out=json-pretty \
    > "$CIVICRM_VARS_JSON_FILE" || exit
