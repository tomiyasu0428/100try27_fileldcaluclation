#!/bin/bash
# マイグレーションを生成して実行するスクリプト

# 仮想環境がある場合はアクティベート
# source venv/bin/activate

# マイグレーション生成
flask db migrate -m "Add crop, cultivation_plan, and schedule models"

# マイグレーション実行
flask db upgrade

echo "Migration completed."
