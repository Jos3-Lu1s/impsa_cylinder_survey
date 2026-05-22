from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError
import base64

class SaleOrderSmart(models.Model):
    _inherit = 'sale.order'

    survey_id = fields.Many2one(
        "impsa.cylinder.survey",
        string="Levantamiento de Origen",
        ondelete="set null",
        copy=False,
        help="Levantamiento técnico del cual se generó esta cotización."
    )
    
    cylinder_survey_count = fields.Integer(
        string="Levantamientos",
        compute="_compute_cylinder_survey_count"
    )
    
    requeriments_work_order=fields.Text(string="Levantamiento/OT", store=True, readonly=True)
    group_requeriments_work_order=fields.Text(string="Grupo Relacionado", store=True, readonly=True)
    
    delivery_days = fields.Integer(
        string="Días de entrega",
        compute="_compute_delivery_days"
    )
    apu_id = fields.Many2one(
        'impsa.apu.survey',
        string="APU Relacionado",
        ondelete="set null",
        copy=False,
    )
    
    apu_survey_count = fields.Integer(
        string="APU",
        compute="_compute_apu_survey_count"
    )
    
    def _message_get_suggested_recipients(self, **kwargs):
        # En esta versión devuelve lista, no dict
        # Simplemente retornamos lista vacía
        return []

    @api.onchange('pricelist_id')
    def _onchange_pricelist_product_domain(self):
        """Dispara el recálculo del dominio en todas las líneas."""
        for line in self.order_line:
            line._compute_product_template_domain()

    @api.depends('survey_id')
    def _compute_cylinder_survey_count(self):
        for record in self:
            record.cylinder_survey_count = 1 if record.survey_id else 0

    @api.depends('apu_id')
    def _compute_apu_survey_count(self):
        for record in self:
            record.apu_survey_count = 1 if record.apu_id else 0

    def action_view_survey(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Levantamiento',
            'res_model': 'impsa.cylinder.survey',
            'view_mode': 'form',
            'res_id': self.survey_id.id,
        }
        
    def action_print_proforma_custom(self):
        return self.env.ref('impsa_cylinder_survey.action_report_proforma_custom').report_action(self)
    
    @api.depends('commitment_date')
    def _compute_delivery_days(self):
        for record in self:
            if record.commitment_date:
                today = date.today()
                commit_date = record.commitment_date.date() if record.commitment_date else None

                if commit_date:
                    record.delivery_days = (commit_date - today).days
                else:
                    record.delivery_days = 0
            else:
                record.delivery_days = 0

    def action_view_apu_survey(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'APU',
            'res_model': 'impsa.apu.survey',
            'view_mode': 'form',
            'res_id': self.apu_id.id,
        }

    @api.onchange('partner_id')
    def _onchange_select_pricelist(self):
            pricelist = self.env['product.pricelist'].search([
                        ('contacto_id', '=', self.partner_id.id)  # ← nombre de tu campo Many2one
                    ], limit=1)
            if self.partner_id:
                self.pricelist_id=pricelist.id
                #raise ValidationError(f"La lista de precios es {pricelist}")
                
    def _get_report_base_filename(self):
        self.ensure_one()
        return self.name

    def action_quotation_send(self):
        self.ensure_one()
    
        # ── Generar PDF pasando el xml_id como string ─────────────────
        report = self.env['ir.actions.report']
        pdf_content, _ = report.sudo()._render_qweb_pdf(
            'impsa_cylinder_survey.action_report_proforma_custom',
            res_ids=[self.id]
        )
    
        # ── Crear adjunto ─────────────────────────────────────────────
        attachment = self.env['ir.attachment'].sudo().create({
            'name': f'{self.name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'sale.order',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
    
        # ── Llamar al wizard nativo con el adjunto reemplazado ────────
        result = super().action_quotation_send()
    
        if isinstance(result, dict) and result.get('context'):
            result['context']['default_attachment_ids'] = [attachment.id]
    
        return result
