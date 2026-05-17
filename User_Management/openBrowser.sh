#!/bin/bash

ps aux | grep [f]irefox && killall -9 firefox
nohup firefox --display=:0 $1 &
