#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量初始化 LLMOps 账号密码

作用：
  1. 从 CSV 读取账号列表（email, name）
  2. 用与项目完全一致的算法生成密码密文与盐值
     （pbkdf2_hmac sha256 10000轮 -> hexlify -> base64）
  3. 默认只生成 Excel 供核对；加 --apply 才真正写入数据库

用法：
  # 1) 先预览，只生成 Excel，绝不动数据库（推荐先跑这个核对）
  python scripts/init_accounts.py --password Abcd1234

  # 2) 核对无误后，真正写入数据库
  python scripts/init_accounts.py --password Abcd1234 --apply

  # 3) 不指定密码，则每个账号随机生成（明文会写进 Excel）
  python scripts/init_accounts.py --apply

注意：Excel 内含明文密码，属于敏感文件，用后请及时删除。
"""

import argparse
import base64
import binascii
import csv
import hashlib
import io
import os
import random
import re
import secrets
import string
import sys
from pathlib import Path

# Windows 控制台下保证中文正常输出
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

# 把 api 根目录加入 sys.path，以便复用项目自身的密码实现
API_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API_ROOT))

# 优先复用项目 pkg.password，保证算法与线上完全一致；取不到则回退到内联实现
try:
    from pkg.password import hash_password as _project_hash_password
    from pkg.password import validate_password as _project_validate_password

    USING_PROJECT = True
except Exception:
    USING_PROJECT = False

    def _project_hash_password(password: str, salt) -> bytes:
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 10000)
        return binascii.hexlify(dk)


PASSWORD_PATTERN = r"^(?=.*[a-zA-Z])(?=.*\d).{8,16}$"


def validate_pwd(pwd: str) -> None:
    """校验密码是否符合项目规则"""
    if re.match(PASSWORD_PATTERN, pwd) is None:
        raise ValueError("密码不符合规则：至少包含 1 个字母、1 个数字，长度 8-16 位")
    if USING_PROJECT:
        _project_validate_password(pwd)


def gen_random_password(length: int = 12) -> str:
    """生成符合规则的随机密码"""
    chars = string.ascii_letters + string.digits
    while True:
        pwd = ''.join(random.choices(chars, k=length))
        if re.match(PASSWORD_PATTERN, pwd):
            return pwd


def build_credential(plain_password: str):
    """返回 (password密文, password_salt)，与 AccountService.update_password 逻辑一致"""
    salt = secrets.token_bytes(16)
    password_salt = base64.b64encode(salt).decode()
    password_hashed = _project_hash_password(plain_password, salt)
    password = base64.b64encode(password_hashed).decode()
    return password, password_salt


def read_accounts(csv_path: Path) -> list:
    """读取账号列表 CSV，需要包含 email 列，name 列可选"""
    accounts = []
    with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = (row.get('email') or '').strip()
            name = (row.get('name') or '').strip()
            if not email:
                continue
            accounts.append({'email': email, 'name': name or email.split('@')[0]})
    return accounts


def write_excel(rows, out_path: Path):
    """把结果写成 Excel"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = "初始化账号"

    headers = ['email', 'name(显示名)', '明文密码(敏感)', 'password(密文)', 'password_salt', '数据库操作']
    ws.append(headers)

    header_fill = PatternFill("solid", fgColor="DDEBF7")
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')

    for r in rows:
        ws.append([
            r['email'], r['name'], r['plain_password'],
            r['password'], r['password_salt'], r['action'],
        ])

    for i, w in enumerate([32, 18, 20, 70, 28, 18], start=1):
        ws.column_dimensions[chr(64 + i)].width = w

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)


def apply_to_db(rows, db_url: str):
    """写入数据库：邮箱已存在则更新密码，不存在则新增账号"""
    import psycopg2

    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    try:
        cur = conn.cursor()
        for r in rows:
            cur.execute("SELECT id FROM account WHERE email = %s", (r['email'],))
            if cur.fetchone() is None:
                cur.execute(
                    "INSERT INTO account (name, email, password, password_salt) "
                    "VALUES (%s, %s, %s, %s)",
                    (r['name'], r['email'], r['password'], r['password_salt']),
                )
                r['action'] = '新增'
            else:
                cur.execute(
                    "UPDATE account SET password = %s, password_salt = %s, name = %s, updated_at = NOW() "
                    "WHERE email = %s",
                    (r['password'], r['password_salt'], r['name'], r['email']),
                )
                r['action'] = '更新'
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="批量初始化 LLMOps 账号密码")
    parser.add_argument(
        '--csv', default=str(API_ROOT / 'scripts' / 'accounts.csv'),
        help='账号列表 CSV（需含 email 列，name 列可选）',
    )
    parser.add_argument(
        '--password', default=None,
        help='统一初始密码（8-16位，含字母+数字）；不指定则每个账号随机生成',
    )
    parser.add_argument(
        '--out', default=str(API_ROOT / 'scripts' / 'init_accounts.xlsx'),
        help='输出 Excel 路径',
    )
    parser.add_argument(
        '--apply', action='store_true',
        help='真正写入数据库（不加则只生成 Excel，绝不改库）',
    )
    parser.add_argument(
        '--db-url',
        default=os.getenv('SQLALCHEMY_DATABASE_URI')
        or 'postgresql://postgres:postgres@localhost:5433/llmops',
        help='数据库连接串',
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"[错误] 找不到账号列表: {csv_path}")
        print("       请复制 scripts/accounts.example.csv 为 accounts.csv 并填入邮箱")
        sys.exit(1)

    accounts = read_accounts(csv_path)
    if not accounts:
        print(f"[错误] 账号列表为空: {csv_path}")
        sys.exit(1)

    if args.password:
        try:
            validate_pwd(args.password)
        except ValueError as e:
            print(f"[错误] {e}")
            sys.exit(1)

    source = '项目 pkg.password' if USING_PROJECT else '脚本内联（与项目一致）'
    print(f"读取到 {len(accounts)} 个账号 | 密码算法来源: {source}")

    rows = []
    for a in accounts:
        pwd = args.password or gen_random_password()
        password, password_salt = build_credential(pwd)
        rows.append({
            'email': a['email'],
            'name': a['name'],
            'plain_password': pwd,
            'password': password,
            'password_salt': password_salt,
            'action': '未写入(待 --apply)',
        })

    if args.apply:
        apply_to_db(rows, args.db_url)
        print(f"[已写入数据库] 共处理 {len(rows)} 个账号")
    else:
        print("[预览模式] 未修改数据库，仅生成 Excel。核对无误后加 --apply 再跑一次。")

    out_path = Path(args.out)
    write_excel(rows, out_path)
    print(f"[Excel 已生成] {out_path}")

    print("\n账号清单：")
    for r in rows:
        print(f"  {r['email']:<32} 密码={r['plain_password']}  [{r['action']}]")
    print("\n提示：Excel 内含明文密码，请妥善保管，用后及时删除。")


if __name__ == '__main__':
    main()
