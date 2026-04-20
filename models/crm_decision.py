from odoo import models, fields, api
from odoo.exceptions import UserError

# HERENCIA DEL WIZARD ESTÁNDAR
class CrmQuotationPartner(models.TransientModel):
    _inherit = 'crm.quotation.partner'

    def action_apply(self):
        """
        Interceptamos el comportamiento estándar del wizard.
        """
        # Lógica nativa (crear, vincular o ignorar el cliente)
        res = super().action_apply()
        
        # Flujo de LEVANTAMIENTO
        if self.env.context.get('open_survey'):
            return {
                'type': 'ir.actions.act_window',
                'name': 'Nuevo Levantamiento',
                'res_model': 'impsa.cylinder.survey',
                'view_mode': 'form',
                'target': 'current',
                'context': {
                    'default_lead_id': self.lead_id.id,
                    'default_partner_id': self.lead_id.partner_id.id if self.lead_id.partner_id else False,
                }
            }
            
        # Flujo de APU
        elif self.env.context.get('open_apu'):
            return {
                'type': 'ir.actions.act_window',
                'name': 'Nueva APU',
                'res_model': 'impsa.apu.survey',
                'view_mode': 'form',
                'target': 'current',
                'context': {
                    'default_lead_id': self.lead_id.id,
                    'default_partner_id': self.lead_id.partner_id.id if self.lead_id.partner_id else False,
                }
            }
            
        # Cotización normal de Odoo, devolvemos el resultado nativo
        return res

# MODELO CRM.LEAD (OPORTUNIDAD)
class CrmDecision(models.Model):
    _inherit = "crm.lead"

    selection_crm = fields.Boolean(
        string="Reparación de cilindro"
    )
    
    selection_type = fields.Selection([
        ('manufacturing', 'Fabricación'),
        ('repair', 'Reparación')
    ],string='Tipo de Cilindro')
    
    is_won_stage = fields.Boolean(
        related='stage_id.is_won',
        store=True
    )
    
    cylinder_survey_ids = fields.One2many(
        'impsa.cylinder.survey',
        'lead_id',
        string="Levantamientos de Cilindro"
    )
    
    apu_survey_ids = fields.One2many(
        'impsa.apu.survey',
        'lead_id',
        string="Levantamientos de APU"
    )
    
    cylinder_survey_count = fields.Integer(
        string="Levantamientos",
        compute="_compute_cylinder_survey_count"
    )
    
    apu_survey_count = fields.Integer(
        string="APU",
        compute="_compute_apu_survey_count"
    )
    
    stage_sequence = fields.Integer(
        related='stage_id.sequence',
        store=True
    )
    
    is_survey = fields.Boolean(
        related='stage_id.is_survey',
        string="Requiere Levantamiento",
        store=False
    )
    is_apu = fields.Boolean(
        related='stage_id.is_apu',
        string="Requiere APU",
        store=False
    )
    is_lose = fields.Boolean(
        related='stage_id.is_lose',
        string="Etapa de Pérdida",
        store=False
    )
    
    @api.depends('cylinder_survey_ids')
    def _compute_cylinder_survey_count(self):
        for rec in self:
            rec.cylinder_survey_count = len(rec.cylinder_survey_ids)
            
    @api.depends('apu_survey_ids')
    def _compute_apu_survey_count(self):
        for rec in self:
            rec.apu_survey_count = len(rec.apu_survey_ids)

    # ACCIONES DE LEVANTAMIENTO
    def action_open_cylinder_survey(self):
        self.ensure_one()

        # Si NO hay cliente establecido, llamamos al modal nativo
        if not self.partner_id:
            action = self.env["ir.actions.actions"]._for_xml_id("sale_crm.crm_quotation_partner_action")
            action['name'] = 'Nuevo Levantamiento'
            action['context'] = dict(self.env.context, open_survey=True)
            
            return action

        # Si SÍ hay cliente, abrimos el formulario normalmente
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

    def action_view_cylinder_surveys(self):
        surveys = self.env['impsa.cylinder.survey'].search([
            ('lead_id', '=', self.id)
        ])

        if len(surveys) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Levantamiento',
                'res_model': 'impsa.cylinder.survey',
                'view_mode': 'form',
                'res_id': surveys.id,
            }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Levantamientos',
            'res_model': 'impsa.cylinder.survey',
            'view_mode': 'tree,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id': self.id
            }
        }
        
    # -------------------------------------------------------------------------
    # ACCIONES DE APU
    # -------------------------------------------------------------------------
    def action_open_apu(self):
        self.ensure_one()

        # Si NO hay cliente establecido, llamamos al modal nativo
        if not self.partner_id:
            action = self.env["ir.actions.actions"]._for_xml_id("sale_crm.crm_quotation_partner_action")
            action['name'] = 'Nueva APU'
            action['context'] = dict(self.env.context, open_apu=True)
            
            return action

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
        
    def action_view_apus(self):
        self.ensure_one()

        apus = self.env['impsa.apu.survey'].search([
            ('lead_id', '=', self.id)
        ])
    
        if len(apus) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'APU',
                'res_model': 'impsa.apu.survey',
                'view_mode': 'form',
                'res_id': apus.id,
            }
    
        return {
            'type': 'ir.actions.act_window',
            'name': 'Análisis de Precios',
            'res_model': 'impsa.apu.survey',
            'view_mode': 'tree,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id': self.id
            }
        }
        
    def action_view_apu(self):
        self.ensure_one()

        if self.apu_survey_ids:
            raise UserError("Ya existe un APU para esta oportunidad.")

        return {
            'type': 'ir.actions.act_window',
            'name': 'APU',
            'res_model': 'impsa.apu.survey',
            'view_mode': 'form',
            'context': {
                'default_lead_id': self.id
            }
        }
        
class CrmStage(models.Model):
    _inherit = 'crm.stage'

    is_survey = fields.Boolean(
        string="Requiere Levantamiento",
    )
    
    is_apu = fields.Boolean(
        string="Requiere APU",
    )
    
    is_lose = fields.Boolean(
        string="Etapa de Pérdida",
    )