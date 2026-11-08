#!/bin/bash
# Idempotent: each step is skipped if already done, so `down`/`up` or `restart` just runs `bench start`.
set -e

SITE=crm.localhost
BENCH=/home/frappe/frappe-bench

# Named volumes / mount points are created root-owned
sudo chown frappe:frappe "$BENCH" "$BENCH/apps" \
    "$BENCH/apps/crm/node_modules" "$BENCH/apps/crm/frontend/node_modules"

cd /home/frappe

if [ ! -d "$BENCH/apps/frappe" ]; then
    bench init --ignore-exist --skip-assets --skip-redis-config-generation --frappe-branch version-16 frappe-bench
fi

cd "$BENCH"

bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379

# Redis runs as its own container; Vite replaces `bench watch`
sed -i '/redis/d;/watch/d;/^vite:/d' Procfile
echo 'vite: cd apps/crm/frontend && yarn dev --host 0.0.0.0 --port 8080' >> Procfile

# Register the bind-mounted CRM checkout as an app
./env/bin/pip install -q -e apps/crm
grep -qx crm sites/apps.txt || printf '\ncrm\n' >> sites/apps.txt

# CRM's frontend links ../../whatsapp/ui and ../../frappe/ui
[ -d apps/whatsapp ] || bench get-app whatsapp --branch main

(cd apps/crm && yarn install --check-files)

# apps/crm exists before it is installed, so the first asset build has to wait until now
[ -f sites/assets/.dev-built ] || { bench build && touch sites/assets/.dev-built; }

if [ ! -d "sites/$SITE" ]; then
    bench new-site $SITE \
        --force \
        --mariadb-root-password 123 \
        --admin-password admin \
        --no-mariadb-socket
fi

bench --site $SITE list-apps | grep -qx crm || bench --site $SITE install-app crm
bench --site $SITE set-config developer_mode 1
bench --site $SITE set-config mute_emails 1
bench --site $SITE set-config server_script_enabled 1
bench --site $SITE clear-cache
bench use $SITE

bench start
