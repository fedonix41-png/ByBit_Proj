#!/bin/bash
# Cron job for daily backups
# Add to crontab: 0 2 * * * /path/to/scripts/cron_backup.sh

cd /home/ozzy/Документы/ByBit-tst
./scripts/backup_db.sh --container >> logs/backup.log 2>&1
