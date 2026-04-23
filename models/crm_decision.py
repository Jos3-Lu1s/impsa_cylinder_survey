from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo import exceptions, _
from odoo.exceptions import ValidationError

# HERENCIA DEL WIZARD ESTÁNDAR
class CrmQuotationPartner(models.TransientModel):
    _inherit = 'crm.quotation.partner'

    def action_apply(self):
        """
        Interceptamos el comportamiento estándar del wizard.
        """
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
        store=False
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
        store=False
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
    
    ganado_state = fields.Boolean(
        related='stage_id.ganado_state',
        store=False,
        string="Ganado",
    )
    
    final_lap = fields.Boolean(
        string="Terminado",
        default=False,
        copy=False,
        tracking=True
    )
    
    def _get_mail_thread_data_attachments(self):
        res = super()._get_mail_thread_data_attachments()
        return res
    
    # Deshabilitar el compositor de mensajes
    _mail_post_access = 'read'
    
    def _message_get_suggested_recipients(self, **kwargs):
        return []
    
    @api.model
    def default_get(self, fields): 
        res = super().default_get(fields)
        if 'name' in fields:
            res['name'] = ' '
        return res
    
    @api.depends('stage_id', 'stage_id.stage_type')
    def _compute_stage_type(self):
        for lead in self:
            lead.is_survey = lead.stage_id.stage_type == 'survey'
            lead.is_apu    = lead.stage_id.stage_type == 'apu'
            lead.is_lose   = lead.stage_id.stage_type == 'lose' 
    
    def action_set_won_rainbowman(self):
        res = super().action_set_won_rainbowman()
        self.sudo().write({'final_lap': True})
        return res

    def action_set_won(self):
        res = super().action_set_won()
        self.sudo().write({'final_lap': True})
        return res
    
    def _sync_stage_from_type(self, stage_type):
        self.ensure_one()

        if stage_type == 'won':
            if not self.final_lap:
                self.action_set_won_rainbowman()
            return

        etapa = self.env['crm.stage'].search([
            ('stage_type', '=', stage_type)
        ], limit=1)

        if etapa and etapa.id != self.stage_id.id:
            self.sudo().with_context(sync_from_survey=True).write({
                'stage_id': etapa.id
            })
    
    """ def write(self, vals):
        if 'stage_id' in vals:
            if self.env.context.get('sync_from_survey'):
                return super().write(vals)

            nueva_etapa = self.env['crm.stage'].browse(vals['stage_id'])

            for lead in self:
                if lead.final_lap:
                    raise exceptions.ValidationError(_(
                        'La oportunidad "%s" ya fue marcada como ganada '
                        'y no puede cambiar de etapa.'
                    ) % lead.name)

                tipo = vals.get('selection_type', lead.selection_type)

                if not tipo and nueva_etapa.stage_type in ('apu', 'survey'):
                    raise exceptions.ValidationError(_(
                        'Debes seleccionar un tipo antes de avanzar '
                        'a la etapa "%s".'
                    ) % nueva_etapa.name)

                if tipo == 'manufacturing' and nueva_etapa.stage_type == 'survey':
                    raise exceptions.ValidationError(_(
                        'La oportunidad "%s" es de tipo Fabricación y no '
                        'puede avanzar a una etapa de Levantamiento.'
                    ) % lead.name)

                if tipo == 'repair' and nueva_etapa.stage_type == 'apu':
                    levantamiento = lead.cylinder_survey_ids.filtered(
                        lambda s: s.state == 'apu'
                    )
                    if not levantamiento:
                        raise exceptions.ValidationError(_(
                            'La oportunidad "%s" es de tipo Reparación y solo '
                            'puede avanzar a APU cuando el levantamiento '
                            'relacionado esté en estado APU.'
                        ) % lead.name)

                if nueva_etapa.stage_type == 'negotiation':
                    lev_cotizado   = lead.cylinder_survey_ids.filtered(lambda s: s.state == 'quoted')
                    apu_confirmado = lead.apu_survey_ids.filtered(lambda a: a.state == 'confirmed')
                    if not lev_cotizado and not apu_confirmado:
                        raise exceptions.ValidationError(_(
                            'La oportunidad "%s" no puede avanzar a '
                            'Negociación hasta que el levantamiento esté '
                            'en Cotización o el APU esté confirmado.'
                        ) % lead.name)

        return super().write(vals) """
    
    def write(self, vals):
        if 'stage_id' in vals:

            if self.env.context.get('sync_from_survey'):
                return super().write(vals)

            nueva_etapa = self.env['crm.stage'].browse(vals['stage_id'])

            for lead in self:

                # ── Bloquear retroceso de etapa ───────────────────────
                if nueva_etapa.sequence < lead.stage_id.sequence:

                    # Definir desde qué etapa ya no se puede regresar
                    bloqueos = {
                        'survey':      'No puedes regresar a Oportunidad desde Levantamiento.',
                        'apu':         'No puedes regresar a Levantamiento o Oportunidad desde APU.',
                        'negotiation': 'No puedes regresar desde Negociación.',
                        'won':         'No puedes regresar desde Ganado.',
                    }

                    mensaje = bloqueos.get(lead.stage_id.stage_type)
                    if mensaje:
                        raise exceptions.ValidationError(_(
                            'La oportunidad "%s" no puede retroceder de etapa. %s'
                        ) % (lead.name, mensaje))

                # ── Bloqueado si ya está ganado ───────────────────────
                if lead.final_lap:
                    raise exceptions.ValidationError(_(
                        'La oportunidad "%s" ya fue marcada como ganada '
                        'y no puede cambiar de etapa.'
                    ) % lead.name)

                tipo = vals.get('selection_type', lead.selection_type)

                # ── Sin tipo no puede avanzar a etapas especiales ─────
                if not tipo and nueva_etapa.stage_type in ('apu', 'survey'):
                    raise exceptions.ValidationError(_(
                        'Debes seleccionar un tipo (Fabricación o Reparación) '
                        'antes de avanzar a la etapa "%s".'
                    ) % nueva_etapa.name)

                # ── Fabricación no puede ir a etapa de levantamiento ──
                if tipo == 'manufacturing' and nueva_etapa.stage_type == 'survey':
                    raise exceptions.ValidationError(_(
                        'La oportunidad "%s" es de tipo Fabricación y no '
                        'puede avanzar a una etapa de Levantamiento.'
                    ) % lead.name)

                # ── Reparación solo puede ir a APU si el levantamiento
                #    relacionado ya está en estado APU ─────────────────
                if tipo == 'repair' and nueva_etapa.stage_type == 'apu':
                    levantamiento_en_apu = lead.cylinder_survey_ids.filtered(
                        lambda s: s.state == 'apu'
                    )
                    if not levantamiento_en_apu:
                        raise exceptions.ValidationError(_(
                            'La oportunidad "%s" es de tipo Reparación y solo '
                            'puede avanzar a APU cuando el levantamiento '
                            'relacionado esté en estado APU.'
                        ) % lead.name)

                # ── Negociación requiere cotización o APU confirmado ──
                if nueva_etapa.stage_type == 'negotiation':
                    lev_cotizado   = lead.cylinder_survey_ids.filtered(
                        lambda s: s.state == 'quoted'
                    )
                    apu_confirmado = lead.apu_survey_ids.filtered(
                        lambda a: a.state == 'confirmed'
                    )
                    if not lev_cotizado and not apu_confirmado:
                        raise exceptions.ValidationError(_(
                            'La oportunidad "%s" no puede avanzar a '
                            'Negociación hasta que el levantamiento esté '
                            'en Cotización o el APU esté confirmado.'
                        ) % lead.name)

        return super().write(vals)
    
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

        if not self.partner_id:
            action = self.env["ir.actions.actions"]._for_xml_id("sale_crm.crm_quotation_partner_action")
            action['name'] = 'Nuevo Levantamiento'
            action['context'] = dict(self.env.context, open_survey=True)
            return action

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
        surveys = self.cylinder_survey_ids 

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
        
    def action_open_apu(self):
        self.ensure_one()

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
        apus = self.apu_survey_ids
    
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
            raise UserError(_("Ya existe un APU para esta oportunidad."))

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

    stage_type = fields.Selection([
        ('survey',  'Requiere Levantamiento'),
        ('apu',     'Requiere APU'),
        ('negotiation', 'Negociación'),
        ('none', 'Oportunidad'),
    ], string='Tipo de etapa', default='none')
    
    is_survey = fields.Boolean(compute='_compute_stage_flags', store=True)
    is_apu    = fields.Boolean(compute='_compute_stage_flags', store=True)
    is_lose   = fields.Boolean(compute='_compute_stage_flags', store=True)
    ganado_state = fields.Boolean(compute='_compute_stage_flags', store=True)
    
    @api.depends('stage_type')
    def _compute_stage_flags(self):
        for stage in self:
            stage.is_survey      = stage.stage_type == 'survey'
            stage.is_apu         = stage.stage_type == 'apu'
            stage.is_lose        = stage.stage_type == 'lose'
            stage.ganado_state   = stage.stage_type == 'negotiation'
            
    @api.constrains('is_won')
    def _check_only_one_won_stage(self):
        for record in self:
            if record.is_won:
                won_stages = self.search([
                    ('is_won', '=', True),
                    ('id', '!=', record.id)
                ])
                if won_stages:
                    raise ValidationError(
                        "Solo puede existir una etapa marcada como ganada."
                    )
                    