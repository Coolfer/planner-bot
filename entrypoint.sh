#!/bin/bash
set -e
mkdir -p /data
chmod 777 /data
export DB_PATH=/data/planner.db
python -c "from db import init_db; init_db()"

# Setup cron
cat > /etc/cron.d/daily-plan << 'EOF'
30 7 * * * root /usr/local/bin/python /app/planner.py plan >> /data/daily_plan.log 2>&1
0 9 * * * root /usr/local/bin/python /app/planner.py consult >> /data/daily_consult.log 2>&1
EOF
chmod 0644 /etc/cron.d/daily-plan
cron

if [ -z "$1" ]; then
    set -- bot
fi

if [ "$1" = "bot" ]; then
    exec python /app/bot.py
elif [ "$1" = "plan" ]; then
    exec python /app/planner.py plan
elif [ "$1" = "consult" ]; then
    exec python /app/planner.py consult
else
    exec python /app/$1
fi
