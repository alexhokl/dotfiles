#!/bin/bash
# handler.sh - OpenCode Skill Logic

# Force HKT timezone
export TZ="Asia/Hong_Kong"

# Get current day of the week (1 = Monday)
DAY_OF_WEEK=$(date +%u)

# Calculate End Time (Midnight HKT)
if [ "$DAY_OF_WEEK" -eq 1 ]; then
    END_TIME=$(gdate -d "today 00:00:00" +"%Y-%m-%d %H:%M:%S")
else
    END_TIME=$(gdate -d "last Monday 00:00:00" +"%Y-%m-%d %H:%M:%S")
fi

# Calculate Start Time (14 days before End Time)
START_TIME=$(gdate -d "$END_TIME 14 days ago" +"%Y-%m-%d %H:%M:%S")

# Output as a JSON string for OpenCode to digest
cat <<EOF
{
  "status": "success",
  "timezone": "HKT",
  "start_time": "$START_TIME",
  "end_time": "$END_TIME"
}
EOF
