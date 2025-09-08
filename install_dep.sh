#!/bin/bash

if [ $(pip list | grep -c "kivy") -eq 0 ]; then
	pip install kivy
fi
if [ $(pip list | grep -c "dotenv") -eq 0 ]; then
	pip install python-dotenv
fi