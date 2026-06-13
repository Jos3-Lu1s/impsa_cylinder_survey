from odoo import models, fields, api, Command, _
from odoo.exceptions import ValidationError

class ApuSurvey(models.Model):
    _name = "impsa.apu.survey"
    _description = "Análisis de Precios Unitarios"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Referencia", required=True, copy=False, readonly=True, default="Nuevo"
    )

    partner_id = fields.Many2one(
        "res.partner", string="Cliente", required=True, tracking=True, ondelete='restrict', context={'search_by_ref': True}, index=True
    )

    partner_email = fields.Char(
        related='partner_id.email',
        string="Correo del Cliente",
        readonly=True
    )

    cylinder_qty_by_group= fields.Integer(
        related='group_id.quantity',
        store=True,
        string="Cantidad de Cilindros",
        tracking=True
    )
    apu_product_id = fields.Many2one(
        'product.template', string='Cilindro a trabajar',tracking=True, ondelete='restrict', domain=[('categ_id.name', '=', 'FABRICACION Y REPARACION')]
    )

    date = fields.Date(string="Fecha", default=fields.Date.context_today, index=True)
    
    lead_id = fields.Many2one(
        'crm.lead',
        string="Oportunidad",
        ondelete='restrict'
    )
      
    lead_count = fields.Integer(
        string="Oportunidades",
        compute="_compute_lead_count"
    )

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Para Cotizar'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True, copy=False, index=True)

    lm_ids = fields.One2many(
        'impsa.apu.survey.line',
        'apu_id',
        string="Registros Relacionados"
    )
    tipo_costo_mo = fields.Selection([
        ('costo_fijo_mo', 'Fijo'),
        ('costo_empleado_mo', 'Por Área')
    ], string='Costo de MO', default='costo_empleado_mo')

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        default=lambda self: self.env.company.currency_id,
        ondelete='restrict'
    )

    costo_fijo_lm = fields.Monetary(
        string="Costo de Mano de Obra (Fijo)",
        currency_field="currency_id"
    )

    survey_id = fields.Many2one(
        "impsa.cylinder.survey",
        string="Levantamiento",
        ondelete="restrict",
        index=True,
        help="Levantamiento técnico origen de este APU."
    )

    group_id = fields.Many2one(
        "impsa.cylinder.group",
        string="Grupo de Cilindros",
        ondelete="restrict",
        index=True,
        help="Grupo de cilindros específico que se está costeando."
    )

    quote_ids = fields.One2many(
        'sale.order',
        'apu_id',
        string="Cotización",
    )

    cylinder_survey_count = fields.Integer(
        string="Levantamientos",
        compute="_compute_cylinder_survey_count"
    )

    quote_count = fields.Integer(
        string="Cotizacion",
        compute="_compute_quote_count"
    )
    
    #Financimiento
    is_financed = fields.Boolean(string="Es financiado", default=False)
    
    porcentaje_gran_subtotal = fields.Float(
        string="Porcentaje (%)",
        digits=(16, 2),
        default=0.0,
        tracking=True
    )

    importe_porcentaje_gran_subtotal = fields.Monetary(
        string="Importe del Porcentaje",
        store=True,
        currency_field="currency_id",
        readonly=True,
        compute='_compute_totales_lm'
    )
    
    subtotal_fin = fields.Monetary(string="Subtotal", store=True, currency_field="currency_id", readonly=True, tracking=True, compute='_compute_totales_lm')
    
    #CAMPOS PARA LOS COSTOS TOTALES DE LOS MATERIALES#
    subtotal_material_lm = fields.Monetary(string="Subtotal Material", store=True, currency_field="currency_id", readonly=True, compute='_compute_totales_lm')
    costos_indirectos_material_lm = fields.Monetary(string="Costos Indirectos Material", store=True, currency_field="currency_id", readonly=True, compute='_compute_totales_lm')
    utilidad_impuestos_material_lm = fields.Monetary(string="Utilidad (A.I.) Material", store=True, currency_field="currency_id", readonly=True, compute='_compute_totales_lm')
    total_material_lm = fields.Monetary(string="Total Material", store=True, currency_field="currency_id", readonly=True, compute='_compute_totales_lm')

    #CAMPOS PARA LOS COSTOS TOTALES DE LA MANO DE OBRA#
    subtotal_mo_lm = fields.Monetary(string="Subtotal M.O.", store=True, currency_field="currency_id", readonly=True, compute='_compute_totales_lm')
    costos_indirectos_mo_lm = fields.Monetary(string="Costos Indirectos M.O.", store=True, currency_field="currency_id", readonly=True, compute='_compute_totales_lm')
    utilidad_impuestos_mo_lm = fields.Monetary(string="Utilidad (A.I.) M.O.", store=True, currency_field="currency_id", readonly=True, compute='_compute_totales_lm')
    total_mo_lm = fields.Monetary(string="Total M.O.", store=True, currency_field="currency_id", readonly=True, compute='_compute_totales_lm')

    #CAMPOS PARA LOS COSTOS TOTALES#
    gran_subtotal_lm = fields.Monetary(string="Gran Subtotal", store=True, currency_field="currency_id", readonly=True, tracking=True, compute='_compute_totales_lm')
    gran_total_lm = fields.Monetary(string="Gran Total", store=True, currency_field="currency_id", readonly=True, tracking=True, compute='_compute_totales_lm')

    porcentaje_cindirectos_material=fields.Many2one(
        'impsa.apu.survey.margins', string='Margen C. Indirectos Mat.',
        tracking=True,
         domain=[('type_cost_margin', '=', 'material'),
         ('type_profit_margin', '=', 'indirect_cost'), ]
    )
    porcentaje_utaimp_material=fields.Many2one(
        'impsa.apu.survey.margins', string='Margen Utilidad Mat.',
        tracking=True,
         domain=[('type_cost_margin', '=', 'material'),
         ('type_profit_margin', '=', 'profit_margin'),]
    )
    porcentaje_cindirectos_mo=fields.Many2one(
        'impsa.apu.survey.margins', string='Margen C. Indirectos M.O.',
        tracking=True,
         domain=[('type_cost_margin', '=', 'labour'),
         ('type_profit_margin', '=', 'indirect_cost'),]
    )
    porcentaje_utaimp_mo=fields.Many2one(
        'impsa.apu.survey.margins', string='Margen Utilidad M.O.',
        tracking=True,
         domain=[('type_cost_margin', '=', 'labour'),
         ('type_profit_margin', '=', 'profit_margin'),]
    )
    
    def _message_get_suggested_recipients(self, **kwargs):
        return []

    @api.onchange('survey_id')
    def _onchange_survey_id_domain(self):
        if not self.survey_id:
            return {'domain': {'apu_product_id': [('categ_id', '=', 'RCH')]}}
        else:
            return {'domain': {'apu_product_id': [('categ_id', '=', 'FCH')]}}

    @api.depends(
        'lm_ids.importe_material_lm', 
        'lm_ids.importe_mo_lm', 
        'costo_fijo_lm',
        'tipo_costo_mo',
        'porcentaje_cindirectos_material',
        'porcentaje_utaimp_material',
        'porcentaje_cindirectos_mo',
        'porcentaje_utaimp_mo',
        'porcentaje_gran_subtotal',
    )
    def _compute_totales_lm(self):
        for order in self:
            subtotal_material = sum(order.lm_ids.mapped('importe_material_lm'))
            subtotal_mo = sum(order.lm_ids.mapped('importe_mo_lm'))
            
            order.subtotal_material_lm = subtotal_material
            order.costos_indirectos_material_lm = subtotal_material * (order.porcentaje_cindirectos_material.percentage or 0.0)
            order.utilidad_impuestos_material_lm = subtotal_material * (order.porcentaje_utaimp_material.percentage or 0.0)
            order.total_material_lm = order.subtotal_material_lm + order.costos_indirectos_material_lm + order.utilidad_impuestos_material_lm

            order.subtotal_mo_lm = subtotal_mo
            order.costos_indirectos_mo_lm = subtotal_mo * (order.porcentaje_cindirectos_mo.percentage or 0.0)
            order.utilidad_impuestos_mo_lm = subtotal_mo * (order.porcentaje_utaimp_mo.percentage or 0.0)
            order.total_mo_lm = order.subtotal_mo_lm + order.costos_indirectos_mo_lm + order.utilidad_impuestos_mo_lm

            order.subtotal_fin = order.total_material_lm + order.total_mo_lm
            
            order.importe_porcentaje_gran_subtotal = (
                order.subtotal_fin * order.porcentaje_gran_subtotal
            )
            
            order.gran_subtotal_lm = order.subtotal_fin + order.importe_porcentaje_gran_subtotal
            order.gran_total_lm = order.gran_subtotal_lm + (order.gran_subtotal_lm*0.16)

    @api.model
    def default_get(self, fields):
        defaults = super().default_get(fields)
        try:
            if not defaults.get('porcentaje_cindirectos_material'):
                defaults['porcentaje_cindirectos_material'] = self.env.ref(
                    'impsa_cylinder_survey.apu_survey_margins_material_indirect_cost'
                ).id
            if not defaults.get('porcentaje_utaimp_material'):
                defaults['porcentaje_utaimp_material'] = self.env.ref(
                    'impsa_cylinder_survey.apu_survey_margins_material_profit'
                ).id
            if not defaults.get('porcentaje_cindirectos_mo'):
                defaults['porcentaje_cindirectos_mo'] = self.env.ref(
                    'impsa_cylinder_survey.apu_survey_margins_labour_indirect_cost'
                ).id
            if not defaults.get('porcentaje_utaimp_mo'):
                defaults['porcentaje_utaimp_mo'] = self.env.ref(
                    'impsa_cylinder_survey.apu_survey_margins_labour_profit'
                ).id
        except ValueError:
            pass
        return defaults

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("impsa.apu.survey")
                    or "Nuevo"
                )

        return super().create(vals_list)

    def action_to_confirmed(self):
        for record in self:
            if not record.lm_ids:
                raise ValidationError(_("Debes agregar al menos una línea en el Cotizador de Materiales."))
            
            lines_without_product = record.lm_ids.filtered(lambda l: not l.product_id)
            if lines_without_product:
                raise ValidationError(_("Todas las líneas del Cotizador de Materiales deben tener un producto seleccionado."))

            lines_without_uom = record.lm_ids.filtered(lambda l: not l.unidad_lm)
            if lines_without_uom:
                raise ValidationError(_("Todas las líneas del Cotizador de Materiales deben tener una unidad de medida seleccionada."))

            order_lines = []
            if record.cylinder_qty_by_group <= 0:
                raise ValidationError(_("Debes colocar un número mayor a 0 en el campo 'Cant. de cilindros'"))
            elif record.gran_total_lm <= 0:
                raise ValidationError(_("El APU: '%s' no puede ser cotizado con total 0, verifica tu lista de materiales") % record.name)

            qty = record.cylinder_qty_by_group or 1.0 
            unit_price = record.gran_subtotal_lm
            product_variant = record.apu_product_id.product_variant_id
            
            lead = record.lead_id or (record.survey_id and record.survey_id.lead_id)

            if not record.quote_ids:
                if not product_variant:
                    raise ValidationError(_("Debes colocar un cilindro a trabajar en el APU: %s") % record.name)
                
                order_lines.append(Command.create({
                    'product_id': product_variant.id,
                    'name': f"Reparación / Fabricación: {product_variant.name} (Ref: {record.name})",
                    'product_uom_qty': qty,
                    'price_unit': unit_price,
                }))

                so_vals = {
                    'partner_id': record.partner_id.id,
                    'opportunity_id': lead.id if lead else False,
                    'apu_id': record.id, 
                    'survey_id': record.survey_id.id,
                    'origin': record.name,  
                    'order_line': order_lines,
                }
                self.env['sale.order'].sudo().create(so_vals)
            else:
                for quote in record.quote_ids:
                    for line in quote.order_line:
                        order_lines.append(Command.update(line.id, {
                            'product_id': product_variant.id,
                            'product_uom_qty': qty,
                            'price_unit': unit_price,
                        }))

                    quote.sudo().write({'order_line': order_lines})
                
            record.write({'state': 'confirmed'})
         
    def action_cancel(self):
        """Cancela el registro"""
        for record in self:
            if not record.survey_id:
                if any(quote.state != 'draft' for quote in record.quote_ids):
                    raise ValidationError(_("No puedes cancelar el %s, ya que tiene cotizaciones fuera de estado 'Borrador'.") % record.name)
            
            record.write({'state': 'cancel'})

    def action_set_draft(self):
        """Permite regresar a borrador desde cualquier estado cancelado o APU"""
        for record in self: 
            record.write({'state': 'draft'})

    @api.depends('survey_id')
    def _compute_cylinder_survey_count(self):
        for record in self:
            record.cylinder_survey_count = 1 if record.survey_id else 0

    @api.depends('quote_ids')
    def _compute_quote_count(self):
        for record in self:
            record.quote_count = len(record.quote_ids)

    def action_view_survey(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Levantamiento',
            'res_model': 'impsa.cylinder.survey',
            'view_mode': 'form',
            'res_id': self.survey_id.id,
        }
    
    def action_view_quote(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cotizaciones',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('apu_id', '=', self.id)],
            'context': {
                'default_apu_id': self.id, 
                'default_survey_id': self.survey_id.id,
                'default_partner_id': self.partner_id.id
            }
        }
        
    def _compute_lead_count(self):
        for record in self:
            record.lead_count = 1 if record.lead_id else 0
            
    def action_view_lead(self):
        self.ensure_one()
    
        if not self.lead_id:
            return
    
        return {
            'type': 'ir.actions.act_window',
            'name': 'Oportunidad',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': self.lead_id.id,
        }
        
    def write(self, vals):
        result = super().write(vals)
    
        if 'state' not in vals:
            return result
    
        mapeo_crm = {
            'confirmed': 'negotiation',
        }
    
        nuevo_state = vals['state']
    
        for apu in self:
            survey = apu.survey_id
    
            if survey:
                # Tras super().write(), los APUs hermanos ya reflejan el nuevo estado
                apus_no_cancelados = survey.sudo().apu_ids.filtered(lambda a: a.state != 'cancel')
                apus_confirmados   = survey.sudo().apu_ids.filtered(lambda a: a.state == 'confirmed')
    
                if nuevo_state == 'confirmed':
                    # Basta con que UN APU esté confirmado para mover el survey a cotización
                    survey.sudo().write({'state': 'quoted'})
    
                elif nuevo_state == 'cancel':
                    if not apus_no_cancelados:
                        # TODOS los APUs están cancelados → cancelar el levantamiento
                        survey.sudo().write({'state': 'cancel'})
                    elif not apus_confirmados:
                        # Quedan APUs activos pero ninguno confirmado → volver a 'apu'
                        survey.sudo().write({'state': 'apu'})
                    # Si todavía hay APUs confirmados, NO tocamos el survey
                    # (sigue en 'quoted' porque aún hay cotización vigente).
    
            # ── Sincronizar CRM ───────────────────────────────────────
            lead = apu.lead_id or (survey and survey.lead_id)
            if lead:
                sync_type = mapeo_crm.get(nuevo_state)
                if sync_type:
                    sync_method = getattr(lead, '_sync_stage_from_type', None)
                    if callable(sync_method):
                        sync_method(sync_type)
    
        return result
    
    @api.onchange('is_financed')
    def _onchange_is_financed(self):
        if not self.is_financed:
            self.porcentaje_gran_subtotal = 0.0