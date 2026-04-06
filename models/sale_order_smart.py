from odoo import models, fields, api

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
    
    apu_id = fields.Many2one(
        'impsa.apu.survey',
        string="APU Relacionado"
    )
    apu_survey_count = fields.Integer(
        string="APU",
        compute="_compute_apu_survey_count"
    )

    def _compute_cylinder_survey_count(self):
        for record in self:
            record.cylinder_survey_count = len(record.survey_id)

    def _compute_apu_survey_count(self):
        for record in self:
            record.apu_survey_count = len(record.apu_id)

    def action_view_survey(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Levantamiento',
            'res_model': 'impsa.cylinder.survey',
            'view_mode': 'form',
            'res_id': self.survey_id.id,
        }
    def action_view_apu_survey(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'APU',
            'res_model': 'impsa.apu.survey',
            'view_mode': 'form',
            'res_id': self.apu_id.id,
        }