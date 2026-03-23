#!/bin/bash

set -e

sudo git clone https://github.com/moevm/mse1h2026-employee.git

cd mse1h2026-employee/src

sudo python3 -m venv .venv

sudo bash -c "source .venv/bin/activate && pip install -r requirements.txt"