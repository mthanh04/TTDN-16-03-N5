# -*- coding: utf-8 -*-
{
    'name': "Quản lý Phòng họp",
    'summary': "Module quản lý phòng họp và lịch đặt phòng",
    'description': """
        Module quản lý phòng họp:
        - Quản lý phòng họp
        - Đặt lịch phòng họp
        - Duyệt yêu cầu đặt phòng
        - Kiểm tra trùng lịch tự động
    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Human Resources',
    'version': '0.1.3',
    'depends': ['base', 'nhan_su', 'tai_san'],
    'external_dependencies': {
        'python': ['google-generativeai'],
    },
    'data': [
        'data/sequence.xml',
        'data/cron.xml',
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/phong_hop.xml',
        'views/lich_phong_hop.xml',
        'views/phieu_muon_phong.xml',
        'views/phong_hop_tai_san.xml',
        'views/lich_su_muon_phong.xml',
        'wizard/phong_hop_ai_suggest_views.xml',
        'views/menu.xml',
    ],
    'pre_init_hook': 'pre_init_hook',
}

