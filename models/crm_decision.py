# [MODIFICADO] Se agregó la importación de 'api'
from odoo import models, fields, api

class CrmDecision(models.Model):
    _inherit = "crm.lead"

    selection_crm = fields.Boolean(
        string="Reparación de cilindro"
    )
    
    selection_type = fields.Selection([
        ('manufacturing', 'Fabricación'),
        ('repair', 'Reparación')
    ],string='Tipo de Cilindro', required=True)
    
    is_won_stage = fields.Boolean(
        related='stage_id.is_won',
        store=True
    )
    
    cylinder_survey_ids = fields.One2many(
        'impsa.cylinder.survey',
        'lead_id',
        string="Levantamientos de Cilindro"
    )
    
    cylinder_survey_count = fields.Integer(
        string="Levantamientos",
        compute="_compute_cylinder_survey_count"
    )
    
    stage_sequence = fields.Integer(
        related='stage_id.sequence',
        store=True
    )
    
    def action_open_cylinder_survey(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nuevo Levantamiento',
            'res_model': 'impsa.cylinder.survey',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_lead_id': self.id,
                'default_partner_id': self.partner_id.id,
            }
        }

    @api.depends('cylinder_survey_ids')
    def _compute_cylinder_survey_count(self):
        for rec in self:
            rec.cylinder_survey_count = len(rec.cylinder_survey_ids)
            
    def action_view_cylinder_surveys(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Levantamientos',
            'res_model': 'impsa.cylinder.survey',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id': self.id
            }
        }
        
    def action_open_apu(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva APU',
            'res_model': 'impsa.apu.survey',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_lead_id': self.id,
                'default_partner_id': self.partner_id.id,
            }
        }