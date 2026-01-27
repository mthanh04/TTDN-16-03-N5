# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import json
import logging
import requests
from datetime import datetime, timedelta
import re
import os

_logger = logging.getLogger(__name__)


# =====================================================
# WIZARD AI GỢI Ý PHÒNG HỌP
# =====================================================
class PhongHopAISuggest(models.TransientModel):
    _name = 'phong_hop.ai.suggest'
    _description = 'AI Gợi ý Phòng họp'

    query = fields.Text(
        "Yêu cầu của bạn",
        required=True,
        placeholder="VD: Tìm phòng họp dưới 50 người, có máy chiếu"
    )

    result_ids = fields.One2many(
        'phong_hop.ai.suggest.line',
        'wizard_id',
        string="Phòng gợi ý"
    )

    state = fields.Selection([
        ('draft', 'Nhập yêu cầu'),
        ('done', 'Có kết quả')
    ], default='draft')

    # -------------------------------------------------
    # API KEY
    # -------------------------------------------------
    def _get_gemini_api_key(self):
        IrConfig = self.env['ir.config_parameter'].sudo()
        return IrConfig.get_param('phong_hop.gemini_api_key') or os.environ.get('GEMINI_API_KEY')

    # -------------------------------------------------
    # LẤY PHÒNG KHẢ DỤNG
    # -------------------------------------------------
    def _get_available_rooms(self):
        """Lấy tất cả phòng sẵn sàng (không kiểm tra theo thời gian)"""
        PhongHop = self.env['phong_hop']
        return PhongHop.search([('trang_thai', '=', 'san_sang')])

    # -------------------------------------------------
    # FORMAT PHÒNG CHO AI
    # -------------------------------------------------
    def _format_rooms_for_ai(self, rooms):
        data = []
        for r in rooms[:30]:  # giới hạn token
            data.append({
                "id": r.id,
                "ten": r.ten_phong,
                "ma": r.ma_phong,
                "suc_chua": r.suc_chua,
                "vi_tri": r.vi_tri or "",
                "tai_san": [ts.tai_san_id.ten_tai_san for ts in r.tai_san_ids]
            })
        return json.dumps(data, ensure_ascii=False)

    # -------------------------------------------------
    # GỌI GEMINI 2.5 FLASH (ĐÚNG CHUẨN)
    # -------------------------------------------------
    def _call_gemini_api(self, prompt, api_key):
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            "models/gemini-2.5-flash:generateContent"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.9,
                "maxOutputTokens": 2048

            }
        }

        response = requests.post(
            f"{url}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(response.text)

        data = response.json()

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            raise Exception(f"Invalid Gemini response: {json.dumps(data)}")

    # -------------------------------------------------
    # KIỂM TRA QUERY
    # -------------------------------------------------
    def _is_room_related(self):
        keywords = [
            'phòng', 'họp', 'meeting', 'room',
            'sức chứa', 'người', 'máy chiếu',
            'đặt', 'tìm'
        ]
        q = (self.query or "").lower()
        return any(k in q for k in keywords)

    # -------------------------------------------------
    # PARSE KẾT QUẢ AI
    # -------------------------------------------------
    def _parse_ai_response(self, ai_text, rooms):
        ai_text = ai_text.strip().replace('```json', '').replace('```', '')
        try:
            data = json.loads(ai_text)
        except json.JSONDecodeError as e:
            _logger.error("AI returned invalid JSON: %s", ai_text)
            raise Exception(f"AI trả JSON không hợp lệ: {e}")

        if "error" in data:
            raise UserError("❌ Câu hỏi không liên quan đến phòng họp.")

        room_map = {r.id: r for r in rooms}
        lines = []

        for item in data.get("rooms", []):
            room = room_map.get(item.get("id"))
            if not room:
                continue

            lines.append((0, 0, {
                "phong_hop_id": room.id,
                "ly_do": item.get("reason", "AI đề xuất"),
                "score": min(max(float(item.get("score", 70)), 0), 100)
            }))

        if not lines:
            raise UserError("AI không tìm được phòng phù hợp.")

        return lines

    # -------------------------------------------------
    # ACTION CHÍNH
    # -------------------------------------------------
    def action_suggest_with_ai(self):
        self.ensure_one()

        api_key = self._get_gemini_api_key()
        if not api_key:
            raise UserError("Chưa cấu hình Gemini API Key.")

        if not self._is_room_related():
            raise UserError("Tôi chỉ hỗ trợ tìm phòng họp.")

        rooms = self._get_available_rooms()
        if not rooms:
            raise UserError("Không có phòng trống.")

        prompt = f"""
Bạn là AI CHỈ dùng để GỢI Ý PHÒNG HỌP.

CHỈ TRẢ JSON theo format:
{{
 "rooms": [
   {{"id": number, "reason": string, "score": number}}
 ]
}}

Nếu yêu cầu KHÔNG liên quan → {{ "error": "unsupported" }}

YÊU CẦU NGƯỜI DÙNG:
"{self.query}"

DANH SÁCH PHÒNG:
{self._format_rooms_for_ai(rooms)}
"""

        try:
            _logger.info("Calling Gemini 2.5 Flash...")
            ai_text = self._call_gemini_api(prompt, api_key)
            lines = self._parse_ai_response(ai_text, rooms)
        except Exception as e:
            _logger.error("Gemini error: %s", e)
            _logger.info("Fallback to simple search")
            lines = self._fallback_simple_search(rooms)

        self.write({
            "result_ids": [(5, 0, 0)] + lines,
            "state": "done"
        })

        return {
            "type": "ir.actions.act_window",
            "res_model": "phong_hop.ai.suggest",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new"
        }

    # -------------------------------------------------
    # FALLBACK
    # -------------------------------------------------
    def _fallback_simple_search(self, rooms):
        q = (self.query or "").lower()
        numbers = re.findall(r'\d+', q)
        min_cap = int(numbers[0]) if numbers else 0

        result = rooms.filtered(lambda r: r.suc_chua >= min_cap)
        result = result.sorted(key=lambda r: r.suc_chua)[:3]

        if not result:
            raise UserError("❌ Không tìm được phòng phù hợp.")

        lines = []
        for idx, r in enumerate(result):
            lines.append((0, 0, {
                "phong_hop_id": r.id,
                "ly_do": f"Phòng phù hợp sức chứa {r.suc_chua} người",
                "score": 85 - idx * 10
            }))
        return lines


# =====================================================
# LINE KẾT QUẢ
# =====================================================
class PhongHopAISuggestLine(models.TransientModel):
    _name = 'phong_hop.ai.suggest.line'
    _description = 'Kết quả gợi ý AI'
    _order = 'score desc'

    wizard_id = fields.Many2one('phong_hop.ai.suggest', required=True, ondelete='cascade')
    phong_hop_id = fields.Many2one('phong_hop', required=True)

    ly_do = fields.Text("Lý do")
    score = fields.Float("Điểm")

    suc_chua = fields.Integer(related='phong_hop_id.suc_chua', string="Sức chứa")
    vi_tri = fields.Char(related='phong_hop_id.vi_tri', string="Vị trí")

    tai_san_info = fields.Char(compute='_compute_tai_san', string="Tài sản")

    @api.depends('phong_hop_id')
    def _compute_tai_san(self):
        for r in self:
            r.tai_san_info = ', '.join(
                ts.tai_san_id.ten_tai_san for ts in r.phong_hop_id.tai_san_ids
            ) if r.phong_hop_id.tai_san_ids else 'Không có'
    
    def action_create_booking(self):
        """Mở form đặt lịch phòng họp với phòng đã được chọn"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Đặt Lịch Phòng Họp',
            'res_model': 'lich_phong_hop',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_phong_hop_id': self.phong_hop_id.id,
                'default_nguoi_dat_id': self.env.user.employee_id.id if self.env.user.employee_id else False,
            }
        }



