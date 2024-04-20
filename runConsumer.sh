#! /usr/bin/bash
source /beegfs/virtualenv/venv/bin/activate
nohup python /beegfs/pipeline/rabbitmq/consumer_run_pipeline.py &
