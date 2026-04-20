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
        "res.partner", string="Cliente", required=True, tracking=True, ondelete='restrict'
    )

    cylinder_qty_by_group= fields.Integer(
        related='group_id.quantity',
        store=True,
        string="Cant. de cilindros",
    )
    apu_product_id = fields.Many2one(
        'product.template', string='Cilindro a trabajar', ondelete='restrict', domain=[('categ_id.name', '=', 'FABRICACION Y REPARACION')]
    )

    date = fields.Date(string="Fecha", default=fields.Date.context_today, index=True)
    
    lead_id = fields.Many2one(
        'crm.lead',
        string="Oportunidad",
        ondelete='cascade'
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
        string="Costo",
        currency_field="currency_id"
    )

    survey_id = fields.Many2one(
        "impsa.cylinder.survey",
        string="Levantamiento",
        ondelete="cascade",
        index=True,
        help="Levantamiento técnico origen de este APU."
    )

    group_id = fields.Many2one(
        "impsa.cylinder.group",
        string="Grupo de Cilindros",
        ondelete="cascade",
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
    gran_subtotal_lm = fields.Monetary(string="Gran Subtotal", store=True, currency_field="currency_id", readonly=True, compute='_compute_totales_lm')
    gran_total_lm = fields.Monetary(string="Gran Total", store=True, currency_field="currency_id", readonly=True, compute='_compute_totales_lm')

    #CAMPOS DE PORCENTAJES PARA MARGENES DE COSTOS
    porcentaje_cindirectos_material=fields.Float(string="Margen C. Indirectos Mat.",digits=(16, 2))
    porcentaje_utaimp_material=fields.Float(string="Margen Utilidad Mat.",digits=(16, 2))
    
    porcentaje_cindirectos_mo=fields.Float(string="Margen C. Indirectos M.O.",digits=(16, 2))
    porcentaje_utaimp_mo=fields.Float(string="Margen Utilidad M.O.",digits=(16, 2))

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
        'porcentaje_utaimp_mo'
    )
    def _compute_totales_lm(self):
        for order in self:
            subtotal_material = sum(order.lm_ids.mapped('importe_material_lm'))
            subtotal_mo = sum(order.lm_ids.mapped('importe_mo_lm'))
            

            order.subtotal_material_lm = subtotal_material
            order.costos_indirectos_material_lm=subtotal_material*order.porcentaje_cindirectos_material
            order.utilidad_impuestos_material_lm=subtotal_material*order.porcentaje_utaimp_material
            order.total_material_lm= order.subtotal_material_lm + order.costos_indirectos_material_lm + order.utilidad_impuestos_material_lm

            order.subtotal_mo_lm = subtotal_mo
            order.costos_indirectos_mo_lm=subtotal_mo*order.porcentaje_cindirectos_mo
            order.utilidad_impuestos_mo_lm=subtotal_mo*order.porcentaje_utaimp_mo
            order.total_mo_lm= order.subtotal_mo_lm + order.costos_indirectos_mo_lm + order.utilidad_impuestos_mo_lm

            order.gran_subtotal_lm=order.total_material_lm+order.total_mo_lm
            order.gran_total_lm = order.gran_subtotal_lm + (order.gran_subtotal_lm*0.16)


    @api.model_create_multi
    def create(self, vals_list):
         # Rescatar valores que serán pisados por el related
        qty_by_group_values = {
            i: vals.pop('cylinder_qty_by_group', None)
            for i, vals in enumerate(vals_list)
        }

        # Generar secuencia
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("impsa.apu.survey")
                    or "Nuevo"
                )

        records = super(ApuSurvey, self).create(vals_list)

        # Reescribir el valor después de que el related lo haya recomputado
        for i, record in enumerate(records):
            qty = qty_by_group_values.get(i)
            if qty is not None:
                record.write({'cylinder_qty_by_group': qty})

        return records
        """ for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("impsa.apu.survey")
                    or "Nuevo"
                )

        return super(ApuSurvey, self).create(vals_list) """

    def action_to_confirmed(self):
        for record in self:
            order_lines = []
            if record.cylinder_qty_by_group <= 0:
                raise ValidationError(_("Debes colocar un número mayor a 0 en el campo 'Cant. de cilindros'"))
            elif record.gran_total_lm <= 0:
                raise ValidationError(_("El APU: '%s' no puede cotizardo con total 0, verfica tu lista de materiales")% record.name)

            #qty = record.group_id.quantity or 1.0 
            qty = record.cylinder_qty_by_group or 1.0 
            unit_price = record.gran_subtotal_lm / qty if qty > 0 else record.gran_subtotal_lm
            if not record.quote_ids:
                product_variant = record.apu_product_id.product_variant_id
                if not product_variant:
                    raise ValidationError(_("El producto de la APU: '%s' no tiene variantes activas válidas.") % record.name)
                
                order_lines.append(Command.create({
                    'product_id': product_variant.id,
                    'name': f"Reparación / Fabricación: {product_variant.name} (Ref: {record.name})",
                    'product_uom_qty': qty,
                    'price_unit': unit_price,
                }))

                so_vals = {
                    'partner_id': record.partner_id.id,
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
                            'product_uom_qty': qty,
                            'price_unit': unit_price,
                        }))

                    quote.sudo().write({'order_line': order_lines})
                """ order_lines.append(Command.update(record.quote_ids.id,{
                    'product_uom_qty': qty,
                    'price_unit': unit_price,
                }))

                so_vals = {
                    'order_line': order_lines,
                }
                record.quote_ids.sudo().write(so_vals)   """  
                
                
            record.write({'state': 'confirmed'})
         
    def action_cancel(self):
        """Cancela el registro"""
        for record in self:
            if record.survey_id:
                selection_options = dict(self.env['impsa.cylinder.survey'].fields_get(allfields=['state'])['state']['selection'])
                state_label = selection_options.get(record.survey_id.state, record.survey_id.state)
                if record.survey_id.state not in ['draft' ,'apu']:
                    raise ValidationError(f"No puedes cancelar el {record.name}, ya que el '{record.survey_id.name}' está en estatus {state_label}")
            else:
                if any(quote.state != 'draft' for quote in record.quote_ids):
                    raise ValidationError(f"No puedes cancelar el {record.name}, ya que tiene cotizaciones fuera de estado 'Borrador'.")
            
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
