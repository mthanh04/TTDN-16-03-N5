#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để force recompute số lượng khả dụng cho tất cả tài sản
Chạy script này trong Odoo shell hoặc qua odoo-bin shell
"""

# Cách 1: Chạy trong Odoo shell
# python odoo-bin shell -d db_user -c odoo.conf
# Sau đó chạy code dưới đây:

# Lấy tất cả tài sản
tai_san_records = env['tai_san'].search([])

print(f"Đang cập nhật {len(tai_san_records)} tài sản...")

# Force recompute cho từng tài sản
for ts in tai_san_records:
    ts._compute_so_luong_muon()
    print(f"  - {ts.ten_tai_san}: Tổng={ts.so_luong}, Đang mượn={ts.so_luong_dang_muon}, Khả dụng={ts.so_luong_kha_dung}")

env.cr.commit()
print("Hoàn thành!")
