from odoo import models, fields, api, exceptions, _
# ---> MEJORA: Se consolidaron las importaciones redundantes de excepciones.

class CrmQuotationPartner(models.TransientModel):
    _inherit = 'crm.quotation.partner'

    def action_apply(self):
        res = super().action_apply()
        
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

class CrmDecision(models.Model):
    _inherit = "crm.lead"

    selection_crm = fields.Boolean(
        string="Reparación de cilindro"
    )
    
    selection_type = fields.Selection([
        ('manufacturing', 'Fabricación'),
        ('repair', 'Reparación'),
        ('material', 'Material de línea'),
    ],string='Tipo de Cilindro')
    
    is_won_stage = fields.Boolean(
        related='stage_id.is_won'
    )
    
    cylinder_survey_ids = fields.One2many(
        'impsa.cylinder.survey',
        'lead_id',
        string="Levantamientos de Cilindro",
        groups="impsa_cylinder_survey.group_cylinder_survey_user"
    )

    apu_survey_ids = fields.One2many(
        'impsa.apu.survey',
        'lead_id',
        string="Levantamientos de APU",
        groups="impsa_cylinder_survey.group_apu_user"
    )    
    cylinder_survey_count = fields.Integer(
        string="Levantamientos",
        compute="_compute_cylinder_survey_count",
        compute_sudo=True
    )
    
    apu_survey_count = fields.Integer(
        string="APU",
        compute="_compute_apu_survey_count",
        compute_sudo=True
    )
    
    stage_sequence = fields.Integer(
        related='stage_id.sequence'
    )
    
    is_survey = fields.Boolean(
        related='stage_id.is_survey',
        string="Requiere Levantamiento"
    )
    is_apu = fields.Boolean(
        related='stage_id.is_apu',
        string="Requiere APU"
    )
    is_lose = fields.Boolean(
        related='stage_id.is_lose',
        string="Etapa de Pérdida"
    )
    ganado_state = fields.Boolean(
        related='stage_id.ganado_state',
        string="Ganado"
    )

    is_user_authorized = fields.Boolean(
        compute='_compute_is_user_authorized',
        string="Usuario Autorizado"
    )
    
    sale_order_ids = fields.One2many(
        'sale.order',
        'opportunity_id',  # campo nativo de Odoo en sale.order
        string="Cotizaciones",
    )

    sale_order_count = fields.Integer(
        string="Cotizaciones",
        compute="_compute_sale_order_count",
        compute_sudo=True
    )
    
    @api.depends('sale_order_ids')
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = len(rec.sudo().sale_order_ids)

    @api.depends('stage_id.authorized_user_ids')
    def _compute_is_user_authorized(self):
        for lead in self:
            if not lead.stage_id.authorized_user_ids:
                lead.is_user_authorized = True
            else:
                lead.is_user_authorized = self.env.user in lead.stage_id.authorized_user_ids
    
    final_lap = fields.Boolean(
        string="Terminado",
        default=False,
        copy=False,
        tracking=True
    )
    
    _mail_post_access = 'read'
    
    def _message_get_suggested_recipients(self, **kwargs):
        return []
    
    @api.model
    def default_get(self, fields): 
        defaults = super().default_get(fields)
        
        stage_id = defaults.get('stage_id') or self.env.context.get('default_stage_id')
    
        if stage_id:
            etapa = self.env['crm.stage'].browse(stage_id)
            if etapa.stage_type != 'none':
                raise exceptions.ValidationError(_(
                    'Solo puedes crear oportunidades en la etapa "Oportunidad". '
                    'No es posible crear directamente en la etapa "%s".'
                ) % etapa.name)
                
        if 'name' in fields and not defaults.get('name'):
            defaults['name'] = ' '
            
        return defaults

    def action_set_won_rainbowman(self):
        res = self.with_context(set_won_official=True).sudo()
        result = super(CrmDecision, res).action_set_won_rainbowman()
        self.sudo().write({'final_lap': True})
        return result

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
    
    def write(self, vals):
        if 'stage_id' in vals:
            if self.env.context.get('sync_from_survey'):
                return super().write(vals)

            nueva_etapa = self.env['crm.stage'].browse(vals['stage_id'])

            for lead in self:
                if nueva_etapa.sequence < lead.stage_id.sequence:
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

                if lead.final_lap:
                    raise exceptions.ValidationError(_(
                        'La oportunidad "%s" ya fue marcada como ganada '
                        'y no puede cambiar de etapa.'
                    ) % lead.name)
                    
                if nueva_etapa.is_won and not self.env.context.get('set_won_official'):
                    raise exceptions.ValidationError(_(
                        'La oportunidad "%s" solo puede marcarse como ganada '
                        'desde la etapa de "Negociación".'
                    ) % lead.name)

                tipo = vals.get('selection_type', lead.selection_type)

                if not tipo and nueva_etapa.stage_type in ('apu', 'survey'):
                    raise exceptions.ValidationError(_(
                        'Debes seleccionar un tipo (Fabricación o Reparación) '
                        'antes de avanzar a la etapa "%s".'
                    ) % nueva_etapa.name)

                if tipo == 'manufacturing' and nueva_etapa.stage_type == 'survey':
                    raise exceptions.ValidationError(_(
                        'La oportunidad "%s" es de tipo Fabricación y no '
                        'puede avanzar a una etapa de Levantamiento.'
                    ) % lead.name)
                    
                if tipo == 'material' and nueva_etapa.stage_type != 'negotiation':
                    raise exceptions.ValidationError(_(
                        'La oportunidad "%s" es de tipo Material de línea y no '
                        'puede avanzar a una etapa de Levantamiento.'
                    ) % lead.name)

                if tipo == 'repair' and nueva_etapa.stage_type == 'apu':
                    levantamiento_en_apu = lead.sudo().cylinder_survey_ids.filtered(
                        lambda s: s.state == 'apu'
                    )
                    if not levantamiento_en_apu:
                        raise exceptions.ValidationError(_(
                            'La oportunidad "%s" es de tipo Reparación y solo '
                            'puede avanzar a APU cuando el levantamiento '
                            'relacionado esté en estado APU.'
                        ) % lead.name)

                if nueva_etapa.stage_type == 'negotiation' and tipo != 'material':
                    lev_cotizado   = lead.sudo().cylinder_survey_ids.filtered(
                        lambda s: s.state == 'quoted'
                    )
                    apu_confirmado = lead.sudo().apu_survey_ids.filtered(
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
            rec.cylinder_survey_count = len(rec.sudo().cylinder_survey_ids)
            
    @api.depends('apu_survey_ids')
    def _compute_apu_survey_count(self):
        for rec in self:
            rec.apu_survey_count = len(rec.sudo().apu_survey_ids)

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
            'view_mode': 'list,form',
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
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id': self.id
            }
        }
        
    def action_view_apu(self):
        self.ensure_one()

        if self.apu_survey_ids:
            raise exceptions.UserError(_("Ya existe un APU para esta oportunidad."))

        return {
            'type': 'ir.actions.act_window',
            'name': 'APU',
            'res_model': 'impsa.apu.survey',
            'view_mode': 'form',
            'context': {
                'default_lead_id': self.id
            }
        }
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            stage_id = (
                vals.get('stage_id') or
                self.env.context.get('default_stage_id')
            )
    
            if stage_id:
                etapa = self.env['crm.stage'].browse(stage_id)
                if etapa.stage_type != 'none':
                    raise exceptions.ValidationError(_(
                        'Solo puedes crear oportunidades en la etapa "Oportunidad". '
                        'No es posible crear directamente en la etapa "%s".'
                    ) % etapa.name)
    
        return super().create(vals_list)
    
    def action_create_quotation(self):
        self.ensure_one()
    
        if not self.partner_id:
            action = self.env["ir.actions.actions"]._for_xml_id("sale_crm.crm_quotation_partner_action")
            action['name'] = 'Nueva Cotización'
            action['context'] = dict(self.env.context)
            return action
    
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva Cotización',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_opportunity_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_team_id': self.team_id.id if self.team_id else False,
                'default_user_id': self.user_id.id if self.user_id else False,
            }
        }
    
    def action_view_quotations(self):
        self.ensure_one()
        orders = self.sale_order_ids
    
        if len(orders) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Cotización',
                'res_model': 'sale.order',
                'view_mode': 'form',
                'res_id': orders.id,
            }
    
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cotizaciones',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('opportunity_id', '=', self.id)],
            'context': {'default_opportunity_id': self.id}
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
    
    authorized_user_ids = fields.Many2many(
        'res.users', 
        string='Usuarios Autorizados',
        help='Si se seleccionan usuarios, solo ellos podrán interactuar con los leads en esta etapa.'
    )
    
    @api.depends('stage_type')
    def _compute_stage_flags(self):
        for stage in self:
            stage.is_survey      = stage.stage_type == 'survey'
            stage.is_apu         = stage.stage_type == 'apu'
            stage.is_lose        = stage.stage_type == 'negotiation'
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
                    raise exceptions.ValidationError(
                        "Solo puede existir una etapa marcada como ganada."
                    )
    #Cambios cambios