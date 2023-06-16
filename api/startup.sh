#! /bin/bash
# python3 update_data_hourly.py cron.log &
# python3 update_data_hourly.py cron.log &
python3 server_init.py
gunicorn -b 0.0.0.0:5008 api:app --workers 1 --timeout 15  &
wait