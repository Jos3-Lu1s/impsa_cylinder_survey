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
    
    requeriments_work_order=fields.Text(string="Levantamiento/OT", store=True, readonly=True)
    group_requeriments_work_order=fields.Text(string="Grupo Relacionado", store=True, readonly=True)

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