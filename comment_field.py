#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick fix: Comment problematic field in tai_san.py
"""

import codecs

file_path = r'd:\TTCNTT7\Odoo_code\TTDN-16-03-N5\addons\tai_san\models\tai_san.py'

# Read
with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()

# Replace field declaration with commented version
content = content.replace(
    '''    # Số lượng mượn qua phòng
    so_luong_muon_qua_phong = fields.Integer(
        "Mượn qua phòng",
        compute='_compute_so_luong_muon_qua_phong',
        store=True,
        help="Số lượng tài sản đang mượn qua phiếu mượn phòng"
    )''',
    '''    # Số lượng mượn qua phòng
    # COMMENTED: Method not implemented yet
    # so_luong_muon_qua_phong = fields.Integer(
    #     "Mượn qua phòng",
    #     compute='_compute_so_luong_muon_qua_phong',
    #     store=True,
    #     help="Số lượng tài sản đang mượn qua phiếu mượn phòng"
    # )'''
)

# Write back
with codecs.open(file_path, 'w', 'utf-8') as f:
    f.write(content)

print("✅ Field commented!")
