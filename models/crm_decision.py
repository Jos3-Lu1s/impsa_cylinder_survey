from odoo import models, fields

class CrmDecision(models.Model):
    _inherit = "crm.lead"

    
    selection_crm = fields.Boolean(
        string="Reparación de cilindro"
    )
    
    is_won_stage = fields.Boolean(
        related='stage_id.is_won',
        store=True
    )
    
    cylinder_survey_count = fields.Integer(
        string="Surveys",
        compute="_compute_cylinder_survey_count"
    )
    
    def action_open_cylinder_survey(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cylinder Survey',
            'res_model': 'impsa.cylinder.survey',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id': self.id
            }
        }
        
    def _compute_cylinder_survey_count(self):
        for rec in self:
            rec.cylinder_survey_count = self.env['impsa.cylinder.survey'].search_count([
                ('lead_id', '=', rec.id)
            ])
            
    def action_view_cylinder_surveys(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cylinder Surveys',
            'res_model': 'impsa.cylinder.survey',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id': self.id
            }
        }