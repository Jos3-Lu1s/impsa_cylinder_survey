from odoo import models, fields

class SaleOrderSmart(models.Model):
    _inherit = 'sale.order'

    survey_id = fields.Many2one(
        'impsa.cylinder.survey',
        string='Levantamiento'
    )
    
    cylinder_survey_count = fields.Integer(
        string="Levantamientos",
        compute="_compute_cylinder_survey_count"
    )
    
    def _compute_cylinder_survey_count(self):
        for record in self:
            record.cylinder_survey_count = len(record.survey_id)

    def action_view_survey(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Levantamiento',
            'res_model': 'impsa.cylinder.survey',
            'view_mode': 'form',
            'res_id': self.survey_id.id,
        }