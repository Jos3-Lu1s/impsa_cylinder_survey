from odoo import models, fields, api

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

    apu_product_id=fields.Many2one('product.template',string='Cilindro a trabajar')

    date = fields.Date(string="Fecha", default=fields.Date.context_today, index=True)

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Para Cotizar'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True, copy=False, index=True)

    lm_ids = fields.One2many(
        'impsa.apu.survey.line',   # modelo hijo
        'apu_id',    # campo Many2one del hijo
        string="Registros Relacionados"
    )
    tipo_costo_mo = fields.Selection([
        ('costo_fijo_mo', 'Fijo'),
        ('costo_empleado_mo', 'Por Área')
    ], string='Costo de MO')

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        default=lambda self: self.env.company.currency_id
    )

    costo_fijo_lm = fields.Monetary(
        string="Costo",
        currency_field="currency_id"
    )

    tiene_producto_linea = fields.Boolean(
        #compute="_compute_tiene_producto_linea",
        store=False
    )
    
    
    #CAMPOS PARA LOS COSTOS TOTALES DE LOS MATERIALES#
    subtotal_material_lm = fields.Monetary(string="Subtotal",store=True,currency_field="currency_id", readonly=True,compute='_compute_totales_lm')
    costos_indirectos_material_lm = fields.Monetary(string="Costos Indirectos",store=True,currency_field="currency_id", readonly=True)
    utilidad_impuestos_material_lm = fields.Monetary(string="utilidad antes de Impuestos",store=True,currency_field="currency_id", readonly=True)
    total_material_lm = fields.Monetary(string="Total",store=True,currency_field="currency_id", readonly=True)

    #CAMPOS PARA LOS COSTOS TOTALES DE LA MANO DE OBRA#
    subtotal_mo_lm = fields.Monetary(string="Subtotal",store=True,currency_field="currency_id", readonly=True, compute='_compute_totales_lm')
    costos_indirectos_mo_lm = fields.Monetary(string="Costos Indirectos",store=True,currency_field="currency_id", readonly=True)
    utilidad_impuestos_mo_lm = fields.Monetary(string="utilidad antes de Impuestos",store=True,currency_field="currency_id", readonly=True)
    total_mo_lm = fields.Monetary(string="Total",store=True,currency_field="currency_id", readonly=True)

    #CAMPOS PARA LOS COSTOS TOTALES#
    gran_subtotal_lm = fields.Monetary(string="Gran Subtotal",store=True,currency_field="currency_id", readonly=True)
    gran_total_lm = fields.Monetary(string="Gran Total",store=True,currency_field="currency_id", readonly=True)

    #CAMPOS DE PORCENTAJES PARA MARGENES DE COSTOS
    porcentaje_cindirectos_material=fields.Float(string="Margen C. Indirectos",digits=(16, 2))
    porcentaje_utaimp_material=fields.Float(string="Margen Utilidad",digits=(16, 2))
    
    porcentaje_cindirectos_mo=fields.Float(string="Margen C. Indirectos",digits=(16, 2))
    porcentaje_utaimp_mo=fields.Float(string="Margen Utilidad",digits=(16, 2))


    @api.depends('lm_ids','costo_fijo_lm','tipo_costo_mo','porcentaje_cindirectos_material','porcentaje_utaimp_material','porcentaje_cindirectos_mo','porcentaje_utaimp_mo')
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

            """ if order.order_line:
                line = order.order_line
                line.price_unit = order.gran_subtotal_lm """

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("impsa.apu.survey")
                    or "Nuevo"
                )

        return super(ApuSurvey, self).create(vals_list)


    #@api.depends('order_line.product_template_id')
    #def _compute_tiene_producto_linea(self):
        #for order in self:
            #order.tiene_producto_linea = any(order.order_line.mapped('product_template_id'))