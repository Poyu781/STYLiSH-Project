#!/bin/bash
date
cd ~/Data-Engineering-Class-Batch13/students/Jimmy
~/miniconda3/envs/stylish/bin/python recommend.py
if [ $? == 0 ]; then
    echo "success"
else
    ~/miniconda3/envs/stylish/bin/python mail_notification.py
    echo "Failed to update data"
fi





