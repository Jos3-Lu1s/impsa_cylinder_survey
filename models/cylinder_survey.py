from odoo import models, fields, api, Command, _
from odoo.exceptions import ValidationError, UserError

class CylinderSurvey(models.Model):
    _name = "impsa.cylinder.survey"
    _description = "Levantamiento de Cilindros (F-05-01)"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Referencia", required=True, copy=False, readonly=True, default="Nuevo"
    )

    partner_id = fields.Many2one(
        "res.partner", string="Cliente", required=True, tracking=True, ondelete='restrict'
    )

    partner_email = fields.Char(
        string="Correo Electrónico",
        related="partner_id.email",
        readonly=True
    )

    cylinder_qty = fields.Integer(
        string="Cantidad", 
        default=1, 
        required=True, 
        tracking=True,
        help="Número de cilindros que comparten exactamente estas mismas características."
    )

    allocated_qty = fields.Integer(
        string="Cilindros Asignados",
        compute="_compute_allocated_qty",
        store=True,
        help="Suma de los cilindros ya distribuidos en grupos."
    )

    group_ids = fields.One2many(
        "impsa.cylinder.group", 
        "survey_id",
        string="Grupos de Cilindros",
    )

    all_operational_record_ids = fields.One2many(
        "impsa.operational.record.line",
        "survey_id",
        string="Resumen de Operaciones",
        help="Vista consolidada de todas las operaciones de todos los grupos."
    )

    image_ids = fields.One2many(
        'impsa.cylinder.image', 
        'survey_id', 
        string="Galería de Imágenes"
    )

    # Camisa (Barrel)
    barrel_inner_diameter = fields.Float(string='Ø Interior')
    barrel_outer_diameter = fields.Float(string='Ø Exterior')
    barrel_length = fields.Float(string='Longitud')
    barrel_image_ids = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes de la Camisa", 
        domain=[('component', '=', 'barrel')]
    )

    # Vástago (Rod)
    diameter_rod = fields.Float(string="Ø Vástago")
    rod_length = fields.Float(string='Longitud de Vástago')
    rod_image_ids = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes del Vástago", 
        domain=[('component', '=', 'rod')]
    )
    diameter_rod2 = fields.Float(string="Ø Vástago 2")
    rod_length2 = fields.Float(string='Longitud de Vástago 2')

    # Émbolo (Piston)
    piston_diameter = fields.Float(string='Ø Émbolo') 
    piston_length = fields.Float(string='Longitud de Émbolo')
    piston_image_ids = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes del Émbolo", 
        domain=[('component', '=', 'piston')]
    )

    # Cabeza (Head)
    head_diameter = fields.Float(string='Ø Cabeza')
    head_length = fields.Float(string='Longitud de Cabeza')
    head_image_ids = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes de la Cabeza", 
        domain=[('component', '=', 'head')]
    )

    # Carrera (Stroke)
    stroke_length = fields.Float(string='Longitud de Carrera')
    stroke_image_ids = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes del Ensamble", 
        domain=[('component', '=', 'stroke')]
    )
    
    accessory_image_ids  = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes de accesorios", 
        domain=[('component', '=', 'accessory')]
    )

    date = fields.Date(string="Fecha", default=fields.Date.context_today, index=True, required=True)
    description = fields.Text(string="Descripción")
    
    date_delivery = fields.Date(string="Fecha de Entrega")

    internal_notes = fields.Html(
        string="Notas Internas",
        help="Espacio para notas detalladas sobre este registro.",
    )

    cylinder_survey_line_ids = fields.One2many(
        "impsa.cylinder.survey.line",
        "survey_id",
        string="Empaques",
    )
    
    cylinder_to = fields.Many2one(
        "impsa.cylinder.options",
        string="Cilindro de",
        ondelete='restrict',
        required=True
    )

    cylinder_to_code = fields.Char(
        string="Código del Cilindro",
        related="cylinder_to.code",
        store=False
    )

    total_tasks = fields.Integer(
        string='Total de Tareas',
        compute='_compute_operational_totals',
        store=True,
        help="Suma total de líneas en el registro operativo.",
        readonly=True
    )

    total_groups = fields.Integer(
        string='Total Grupos',
        compute='_compute_dashboard_totals',
        store=True,
        help="Cantidad de grupos de cilindros definidos."
    )

    total_packings = fields.Integer(
        string='Total Empaques',
        compute='_compute_dashboard_totals',
        store=True,
        help="Cantidad de líneas de empaques solicitados."
    )

    state = fields.Selection([
        ('draft', 'Levantamiento'),
        ('apu', 'APU'),
        ('quoted', 'Cotización'),
        ('confirmed', 'Orden de Trabajo'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True, copy=False, index=True, group_expand='_expand_states')

    cylinder_type = fields.Selection([
        ('hydraulic', 'Hidráulico'),
        ('pneumatic', 'Neumático')
    ],string='Tipo de Cilindro', required=True)

    is_standardized = fields.Boolean(
        string='Normalizado'
    )
    
    num_section = fields.Integer(
        string='Número de Secciones',
        default=1, 
    )
    
    purchase_order_create = fields.Boolean(
        string='Orden de Compra Creada',
        default=False,
    )
    
    section_ids = fields.One2many(
        'impsa.cylinder.section',
        'survey_id',
        string='Secciones del Cilindro',
        copy=True
    )
    
    purchase_order_ids = fields.One2many(
        "purchase.order",
        "survey_id",
        string="Órdenes de Compra"
    )

    purchase_order_count = fields.Integer(
        compute="_compute_purchase_order_count"
    )

    lead_id = fields.Many2one(
        'crm.lead',
        string="Oportunidad",
        ondelete='set null'
    )
    
    has_confirmed_order = fields.Boolean(
        compute="_compute_has_confirmed_order"
    )
    
    apu_ids = fields.One2many(
        'impsa.apu.survey',
        'survey_id',
        string="Análisis de Precios (APUs)"
    )

    lead_count = fields.Integer(
        string="Oportunidades",
        compute="_compute_lead_count"
    )
    
    apu_count = fields.Integer(
        string="Cantidad de APUs",
        compute="_compute_apu_count"
    )

    accessory_line_ids = fields.One2many(
        "impsa.cylinder.accessory",
        "survey_id",
        string="Lista de Accesorios y Características",
        copy=True
    )

    sale_order_ids = fields.One2many(
        "sale.order",
        "survey_id",
        string="Cotizaciones"
    )

    sale_order_count = fields.Integer(
        string="Cantidad de Cotizaciones",
        compute="_compute_sale_order_count"
    )

    ''' ------------------------
        COMPUTE METHODS
    -------------------------'''

    @api.depends('sale_order_ids')
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = len(rec.sale_order_ids)
    
    @api.depends('group_ids', 'cylinder_survey_line_ids')
    def _compute_dashboard_totals(self):
        """Calcula las métricas rápidas para las tarjetas superiores en la vista form."""
        for rec in self:
            rec.total_groups = len(rec.group_ids)
            rec.total_packings = len(rec.cylinder_survey_line_ids)

    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for record in self:
            record.purchase_order_count = len(record.purchase_order_ids)

    @api.depends('lead_id')
    def _compute_lead_count(self):
        for rec in self:
            rec.lead_count = 1 if rec.lead_id else 0
            
    @api.depends('apu_ids')
    def _compute_apu_count(self):
        for rec in self:
            rec.apu_count = len(rec.apu_ids)

    @api.depends('group_ids.operational_record_ids', 'group_ids.quantity')
    def _compute_operational_totals(self):
        for record in self:
            total_tasks = 0
            for group in record.group_ids:
                total_tasks += len(group.operational_record_ids)
            record.total_tasks = total_tasks
        
    @api.depends('group_ids.quantity')
    def _compute_allocated_qty(self):
        for survey in self:
            survey.allocated_qty = sum(survey.group_ids.mapped('quantity'))
            
    def _compute_has_confirmed_order(self):
        for record in self:
            existing = self.search([
                ('state', '=', 'confirmed'),
                ('id', '!=', record.id)
            ], limit=1)
            record.has_confirmed_order = bool(existing)

    @api.model
    def _expand_states(self, states, domain, order=None):
        """
        Fuerza a la vista Kanban a cargar las columnas en este orden exacto,
        garantizando que aparezcan incluso si no tienen registros (Count = 0).
        """

        return ['draft', 'apu', 'quoted', 'confirmed'] 
        # return ['draft', 'apu', 'quoted', 'confirmed', 'cancel']
            
    @api.onchange('num_section', 'cylinder_to')
    def _onchange_generate_sections(self):
        """
        Genera dinámicamente las líneas del cilindro telescópico 
        basado en el número de secciones indicadas.
        """
        # 1. Si no es Telescópico, limpiamos las secciones y salimos.
        if self.cylinder_to and self.cylinder_to.code != 'CE-T':
            self.num_section = 0
            self.section_ids = [Command.clear()]
            return

        if self.num_section == 0:
            self.num_section = 1

        # 2. Limitamos el número de secciones
        if self.num_section < 1 or self.num_section > 5:
            # Limpiamos las líneas para no generar basura o colapsar la vista con 1000 líneas
            self.section_ids = [Command.clear()] 
            return {
                'warning': {
                    'title': "Límite de Secciones Excedido",
                    'message': "Por cuestiones de diseño, un cilindro telescópico no puede tener menos de 1 ni más de 5 secciones. Por favor, corrige el número."
                }
            }

        # 3. Preparar la creación de líneas usando odoo.Command
        commands = [Command.clear()] # Primero limpiamos lo que haya
        
        # Diccionario para automatizar nombres (Soporta hasta 5 extensiones)
        ordinales = {1: 'Primera', 2: 'Segunda', 3: 'Tercera', 4: 'Cuarta', 5: 'Quinta'}
        
        # Total de registros a crear = 1 (Principal) + num_section
        total_records = self.num_section + 1
        
        for i in range(total_records):
            if i == 0:
                # Índice 0 siempre es la Camisa Principal
                name = 'Camisa Principal'
                sec_type = 'main'
            elif i == total_records - 1:
                # El último índice siempre es la Última Extensión
                name = f'{ordinales.get(i, str(i) + "a")} Extensión (Última)'
                sec_type = 'last'
            else:
                # Cualquier cosa en medio son Extensiones Intermedias
                name = f'{ordinales.get(i, str(i) + "a")} Extensión'
                sec_type = 'intermediate'
                
            # Agregamos el comando de creación a la lista
            commands.append(Command.create({
                'sequence': (i + 1) * 10, # 10, 20, 30... para mantener el orden
                'name': name,
                'section_type': sec_type,
            }))
            
        # Asignamos la lista de comandos al campo One2many
        self.section_ids = commands

    @api.onchange('cylinder_to')
    def _onchange_clear_hidden_fields(self):
        """
        Evita guardar 'datos fantasma'. Cuando el usuario cambia el tipo de cilindro,
        resetea los valores de las pestañas o campos que quedarán ocultos.
        """
        for rec in self:
            if not rec.cylinder_to or not rec.cylinder_to.code:
                continue

            code = rec.cylinder_to.code

            # 1. Si NO es Telescópico, limpiamos sus secciones
            if code != 'CE-T':
                rec.num_section = 1
                rec.section_ids = [Command.clear()]
                
            # 2. Si NO es Doble Vástago, limpiamos las medidas del Vástago 2
            if code != 'CE-DV':
                rec.diameter_rod2 = 0.0
                rec.rod_length2 = 0.0

            # 3. Si NO es Otros (CE-OT), vaciamos la tabla de accesorios especiales
            if code != 'CE-OT':
                rec.accessory_line_ids = [Command.clear()]
                
            # 4. Si ES Telescópico o ES Otros, limpiamos las medidas de un cilindro estándar
            if code in ['CE-T', 'CE-OT']:
                rec.barrel_inner_diameter = 0.0
                rec.barrel_outer_diameter = 0.0
                rec.barrel_length = 0.0
                rec.diameter_rod = 0.0
                rec.rod_length = 0.0
                rec.piston_diameter = 0.0
                rec.piston_length = 0.0
                rec.head_diameter = 0.0
                rec.head_length = 0.0
                
                # El Telescópico SÍ usa carrera global, pero OTROS no.
                if code == 'CE-OT':
                    rec.stroke_length = 0.0

    ''' ------------------------
        CONSTRAINS
    -------------------------'''

    # Restricción de seguridad para evitar errores de captura
    @api.constrains('cylinder_qty')
    def _check_cylinder_qty(self):
        for record in self:
            if record.cylinder_qty <= 0:
                raise ValidationError(_("La cantidad de cilindros a evaluar debe ser al menos 1."))

    @api.constrains('cylinder_qty', 'allocated_qty')
    def _check_quantities(self):
        """Previene que el usuario agrupe más cilindros de los que existen en el total."""
        for survey in self:
            if survey.allocated_qty > survey.cylinder_qty:
                raise ValidationError(
                    f"Inconsistencia: Has asignado {survey.allocated_qty} cilindros en los grupos, "
                    f"pero el total declarado es de solo {survey.cylinder_qty}."
                )

    @api.constrains('cylinder_to', 'barrel_inner_diameter', 'barrel_outer_diameter', 'diameter_rod', 'diameter_rod2', 'piston_diameter')
    def _check_standard_physics(self):
        """Valida que las medidas de un cilindro estándar tengan sentido físico."""
        for rec in self:
            if rec.cylinder_to_code in ['CE-DE', 'CE-SE', 'CE-DV']:
                
                # 1. Grosor de pared de la Camisa
                if rec.barrel_inner_diameter and rec.barrel_outer_diameter:
                    if rec.barrel_inner_diameter >= rec.barrel_outer_diameter:
                        raise ValidationError(_("Error Físico: El Ø Interior de la Camisa (%(int)s) no puede ser mayor o igual a su Ø Exterior (%(ext)s).") % {
                            'int': rec.barrel_inner_diameter, 'ext': rec.barrel_outer_diameter
                        })
                
                # 2. Vástago vs Camisa
                if rec.diameter_rod and rec.barrel_inner_diameter:
                    if rec.diameter_rod >= rec.barrel_inner_diameter:
                        raise ValidationError(_("Error de Ensamble: El Vástago (Ø %(rod)s) no cabe dentro de la Camisa (Ø Int %(barrel)s).") % {
                            'rod': rec.diameter_rod, 'barrel': rec.barrel_inner_diameter
                        })
                
                # Vástago 2 vs Camisa (Solo para Doble Vástago)
                if rec.cylinder_to_code == 'CE-DV' and rec.diameter_rod2 and rec.barrel_inner_diameter:
                    if rec.diameter_rod2 >= rec.barrel_inner_diameter:
                        raise ValidationError(_("Error de Ensamble: El Vástago 2 (Ø %(rod)s) no cabe dentro de la Camisa (Ø Int %(barrel)s).") % {
                            'rod': rec.diameter_rod2, 'barrel': rec.barrel_inner_diameter
                        })

                # 3. Émbolo vs Camisa
                if rec.piston_diameter and rec.barrel_inner_diameter:
                    if rec.piston_diameter > rec.barrel_inner_diameter:
                        raise ValidationError(_("Error de Ensamble: El Émbolo (Ø %(piston)s) es más grande que el hueco de la Camisa (Ø Int %(barrel)s).") % {
                            'piston': rec.piston_diameter, 'barrel': rec.barrel_inner_diameter
                        })

    @api.constrains(
        'cylinder_to', 'barrel_inner_diameter', 'barrel_outer_diameter', 'barrel_length',
        'diameter_rod', 'rod_length', 'diameter_rod2', 'rod_length2', 'piston_diameter', 'piston_length', 
        'head_diameter', 'head_length', 'stroke_length', 'section_ids',
        'accessory_line_ids'
    )
    def _check_required_dimensions_by_type(self):
        for rec in self:
            if not rec.cylinder_to or not rec.cylinder_to.code:
                continue
                
            code = rec.cylinder_to.code
            missing_components = []

            # Evaluamos por bloque de pieza
            if code == 'CE-OT':
                if not rec.accessory_line_ids:
                    raise ValidationError(
                        _("Para el tipo '%s', es obligatorio agregar al menos una "
                          "línea en la tabla de 'Accesorios / Características'.") 
                        % rec.cylinder_to.name
                    )

            elif code == 'CE-T':
                if not rec.section_ids:
                    raise ValidationError(
                        _("Para cilindros Telescópicos, debe agregar al menos una sección.")
                    )
                if rec.stroke_length <= 0.0:
                    missing_components.append('Carrera Total')

            elif code in ['CE-DE', 'CE-SE', 'CE-DV']:
                if rec.barrel_inner_diameter <= 0.0 or rec.barrel_outer_diameter <= 0.0 or rec.barrel_length <= 0.0:
                    missing_components.append('Camisa')
                if rec.diameter_rod <= 0.0 or rec.rod_length <= 0.0:
                    missing_components.append('Vástago')
                    
                if code == 'CE-DV':
                    if rec.diameter_rod2 <= 0.0 or rec.rod_length2 <= 0.0:
                        missing_components.append('Vástago 2')
                        
                if rec.piston_diameter <= 0.0 or rec.piston_length <= 0.0:
                    missing_components.append('Émbolo')
                if rec.head_diameter <= 0.0 or rec.head_length <= 0.0:
                    missing_components.append('Cabeza')
                if rec.stroke_length <= 0.0:
                    missing_components.append('Carrera')

            # Si se recolectaron errores, lanzar la excepción
            if missing_components:
                componentes = "\n- ".join(missing_components)
                raise ValidationError(
                    _("Faltan medidas mayores a 0 para el cilindro '%(name)s'.\n"
                      "Por favor revisa lo siguiente:\n- %(components)s") % {
                          'name': rec.cylinder_to.name,
                          'components': componentes
                      }
                )
    
    @api.constrains('section_ids')
    def _check_telescopic_physics(self):
        """
        Valida que las secciones de un cilindro telescópico sean físicamente posibles.
        El diámetro exterior de la etapa N debe caber dentro del diámetro interior de la etapa N-1.
        """
        for survey in self:
            if survey.cylinder_to_code == 'CE-T' and len(survey.section_ids) > 1:
                # Asegurarnos de que iteramos en el orden correcto (de fuera hacia adentro)
                sections = survey.section_ids.sorted(lambda s: s.sequence)

                for section in sections:
                    if section.inner_diameter and section.outer_diameter:
                        if section.inner_diameter >= section.outer_diameter:
                            raise ValidationError(_("Error Físico en '%(name)s': El Ø Interior (%(int)s) no puede ser mayor o igual a su Ø Exterior (%(ext)s).") % {
                                'name': section.name, 'int': section.inner_diameter, 'ext': section.outer_diameter
                            })
                
                for i in range(1, len(sections)):
                    prev_sec = sections[i-1] # Etapa exterior (ej. Camisa Principal)
                    curr_sec = sections[i]   # Etapa interior (ej. Primera Extensión)
                    
                    if curr_sec.outer_diameter >= prev_sec.outer_diameter:
                        raise ValidationError(
                            f"Incoherencia física: El Ø Exterior de la '{curr_sec.name}' ({curr_sec.outer_diameter}) "
                            f"no puede ser mayor o igual al Ø Exterior de su antecesor '{prev_sec.name}' ({prev_sec.outer_diameter})."
                        )
                    
                    # 2. Validación estricta de ensamble (OD actual < ID anterior)
                    # prev_sec siempre tendrá inner_diameter porque no puede ser la 'last'
                    if prev_sec.inner_diameter and curr_sec.outer_diameter >= prev_sec.inner_diameter:
                        raise ValidationError(
                            f"Error de Ensamble: La '{curr_sec.name}' tiene un Ø Exterior ({curr_sec.outer_diameter}) "
                            f"que no cabe en el Ø Interior de su antecesor '{prev_sec.name}' ({prev_sec.inner_diameter}).\n"
                            f"¡Revisa las medidas!"
                        )
                
    @api.constrains('num_section', 'cylinder_to')
    def _check_num_section_limits(self):
        for record in self:
            # Solo aplicamos la regla estricta si es Telescópico
            if record.cylinder_to and record.cylinder_to.code == 'CE-T':
                if record.num_section < 1 or record.num_section > 5:
                    raise ValidationError(
                        "Integridad de datos: El número de secciones para un "
                        "cilindro telescópico debe estar estrictamente entre 1 y 5."
                    )

    ''' ------------------------
        ACTIONS
    -------------------------'''

    def action_view_purchase_orders(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes de Compra',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('survey_id', '=', self.id)],
        }

    def action_view_lead(self):
        self.ensure_one()
        
        if self.lead_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Oportunidad',
                'res_model': 'crm.lead',
                'view_mode': 'form',
                'res_id': self.lead_id.id,
                'target': 'current',
            }
            
    def action_view_apus(self):
        self.ensure_one()
        if self.apu_ids:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Análisis de Precios Unitarios',
                'res_model': 'impsa.apu.survey',
                'view_mode': 'list,form',
                'domain': [('survey_id', '=', self.id)],
                'context': {'default_survey_id': self.id, 'default_partner_id': self.partner_id.id}
            }

    def action_view_sale_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cotizaciones'),
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('survey_id', '=', self.id)],
            'context': {
                'default_survey_id': self.id, 
                'default_partner_id': self.partner_id.id
            }
        }

    def action_confirm(self):
        """Valida e inicializa productos para pasar a Orden de Trabajo."""
        for record in self:
            existing_order = self.search([
                ('state', '=', 'confirmed'),
                ('id', '!=', record.id)
            ], limit=1)
            if existing_order:
                raise ValidationError(
                    "Ya existe una Orden de Trabajo confirmada. No puedes crear otra."
                )
            # 1. Validaciones
            if not record.group_ids:
                raise ValidationError("Define al menos un Grupo de Cilindros.")
            if not any(group.operational_record_ids for group in record.group_ids):
                raise ValidationError("Los grupos no tienen tareas operativas asignadas.")
            if record.allocated_qty != record.cylinder_qty:
                raise ValidationError(
                    f"Debes asignar exactamente {record.cylinder_qty} cilindros. "
                    f"Actualmente hay {record.allocated_qty}."
                )
            
            # 2. Creación de Productos en Lote
            Product = self.env['product.product']
            category = self.env['product.category'].search([('name', '=', 'SELLOS')], limit=1)
            categ_id = category.id if category else False

            # Extraer códigos de los empaques de este registro
            lines = record.cylinder_survey_line_ids
            

            lines_with_code = lines.filtered(lambda l: l.code_label)
            lines_without_code = lines.filtered(lambda l: not l.code_label)

            
            # en vez de buscar producto por producto se hace una busqueda masiva
            codes = lines_with_code.mapped('code_label')
            existing_products = Product.search([('default_code', 'in', codes)])
            product_map = {p.default_code: p for p in existing_products}
            seen_codes = set(product_map.keys())

            # Preparar productos a crear
            products_to_create_vals = []
            for line in lines_with_code:
                code = line.code_label
                if code not in seen_codes:
                    seen_codes.add(code)
                    products_to_create_vals.append({
                        'name': line.description_label or f"Empaque {code}",
                        'default_code': code,
                        'type': 'consu', 
                        'categ_id': categ_id,
                    })
                    
            for line in lines_without_code:
                # Si no tiene código, se le asigna un nombre genérico y se deja el código en blanco
                products_to_create_vals.append({
                    'name': line.description_label or "Empaque sin Código",
                    'default_code': False,
                    'type': 'consu', 
                    'categ_id': categ_id,
                })

            # Crear en lote
            if products_to_create_vals:
                new_products = Product.create(products_to_create_vals)
                for p in new_products:
                    product_map[p.default_code] = p
            else:
                new_products = self.env['product.product']
                    
            products_no_code_iter = iter([p for p in new_products if not p.default_code]) if products_to_create_vals else iter([])

            # Asignar productos a las líneas
            """ for line in lines:
                line.product_id = product_map[line.code_label] """
                
            for line in lines:
                if line.code_label:
                    line.product_id = product_map.get(line.code_label, False)
                else:
                    line.product_id = next(products_no_code_iter, False)
            
            if record.group_ids:
                count_apu_confirmed = 0
                for group in record.group_ids:
                    if group.apu_id and group.apu_id.state == 'confirmed':
                        count_apu_confirmed += 1
                if count_apu_confirmed == 0:
                    raise ValidationError(_("Debe existir al menos 1 APU en estado 'Para Cotizar' (aprobado) para poder confirmar la Orden de Trabajo."))

            # 3. Cambio de Estado                
            record.write({'state': 'confirmed'})
    
    def action_to_apu(self):
        """Pasa de Levantamiento a APU y genera los registros de costeo."""
        for record in self:
            if not record.group_ids:
                raise ValidationError(_("No puedes enviar a APU un levantamiento sin grupos."))
            
            if record.allocated_qty != record.cylinder_qty:
                raise ValidationError(_(
                    "La cantidad de cilindros asignados en los grupos (%s) "
                    "no coincide con el total declarado (%s)."
                ) % (record.allocated_qty, record.cylinder_qty))

            # Lógica de creación de APU por cada grupo
            for group in record.group_ids:
                # Evitar duplicar APUs si el usuario regresó a borrador y volvió a avanzar
                if not group.apu_id:
                    apu_vals = {
                        'survey_id': record.id,
                        'group_id': group.id,
                        'partner_id': record.partner_id.id,
                        # Puedes inyectar más campos iniciales aquí si lo deseas
                    }
                    new_apu = self.env['impsa.apu.survey'].create(apu_vals)
                    group.apu_id = new_apu.id

            record.write({'state': 'apu'})

    def action_quoted(self):
        """Pasa de APU a Cotización y genera el Sale Order automáticamente."""
        for record in self:
            if not record.group_ids:
                raise ValidationError(_("Operación inválida: No hay grupos definidos."))
            
            # Extraer APUs que estén en estado 'confirmed'
            confirmed_apus = record.apu_ids.filtered(lambda a: a.state == 'confirmed')
            
            if not confirmed_apus:
                raise ValidationError(_("Para generar una cotización, debe existir al menos una APU en estado 'Para Cotizar' (Confirmada)."))

            # Validación de Productos en APU
            apus_without_product = confirmed_apus.filtered(lambda a: not a.apu_product_id)
            if apus_without_product:
                apu_names = ", ".join(apus_without_product.mapped('name'))
                raise ValidationError(
                    _("Las siguientes APUs no tienen un 'Cilindro a trabajar' asignado: %s. "
                      "Debe asignar un producto para poder cotizar.") % apu_names
                )

            # Preparar Líneas de Venta
            order_lines = []
            for apu in confirmed_apus:
                # sale.order.line requiere product.product, no product.template
                product_variant = apu.apu_product_id.product_variant_id
                if not product_variant:
                    raise ValidationError(_("El producto de la APU '%s' no tiene variantes activas válidas.") % apu.name)

                # gran_subtotal_lm es el costo total del grupo.
                # Si el grupo tiene N cilindros, dividimos el precio para que el total de la línea sea exacto.
                qty = apu.group_id.quantity or 1.0
                unit_price = apu.gran_subtotal_lm / qty if qty > 0 else apu.gran_subtotal_lm

            #     order_lines.append(Command.create({
            #         'product_id': product_variant.id,
            #         'name': f"Reparación / Fabricación: {product_variant.name} (Ref: {apu.name})",
            #         'product_uom_qty': qty,
            #         'price_unit': unit_price,
            #     }))

            # # Crear el Sale Order (Cotización)
            # so_vals = {
            #     'partner_id': record.partner_id.id,
            #     'survey_id': record.id, # Enlace trazable
            #     'origin': record.name,  # Documento origen estándar
            #     'order_line': order_lines,
            # }
            
            # self.env['sale.order'].sudo().create(so_vals)

            for group in record.group_ids:
                if not group.operational_record_ids:
                    raise ValidationError(_(
                        "El grupo '%s' no tiene tareas operativas asignadas. "
                        "APU requiere el listado de trabajos para costear."
                    ) % group.name)
            
            record.write({'state': 'quoted'})

    def action_set_draft(self):
        """Permite regresar a borrador desde cualquier estado cancelado o APU"""
        for record in self: 
            record.write({'state': 'draft'})

    def action_cancel(self):
        """Cancela el registro"""
        for record in self:
            # Bloqueamos la cancelación solo si ya es Orden de Trabajo
            if record.state == 'confirmed':
                raise ValidationError(_("No puedes cancelar un registro que ya es una Orden de Trabajo confirmada. Reviértelo primero."))
            record.write({'state': 'cancel'})

    def action_create_purchase_order(self):
        """Crea Órdenes de Compra agrupadas por proveedor del empaque."""
        self.ensure_one()
        
        if self.purchase_order_create:
            raise UserError(_("Ya se generó una Orden de Compra para este registro."))

        if not self.cylinder_survey_line_ids:
             raise UserError(_("No hay empaques para generar órdenes de compra."))

        # Agrupar líneas por proveedor
        lines_by_supplier = {}
        planned_datetime = fields.Datetime.to_datetime(self.date_delivery) if self.date_delivery else fields.Datetime.now()

        for line in self.cylinder_survey_line_ids:
            seller = line.product_id.seller_ids[:1]
            if not seller:
                raise UserError(_(
                    "El producto '%(prod)s' no tiene un proveedor definido (pestaña Compras).",
                    prod=line.product_id.display_name
                ))

            supplier = seller.partner_id
            if supplier not in lines_by_supplier:
                lines_by_supplier[supplier] = []

            lines_by_supplier[supplier].append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'product_qty': line.unit_total,
                'price_unit': seller.price, #Usar precio del vendor, NO el standard_price (costo).
                'date_planned': planned_datetime,
            }))

        # Crear las POs iterando por cada proveedor detectado.
        created_pos = self.env['purchase.order']
        for supplier, po_lines in lines_by_supplier.items():
            po = self.env['purchase.order'].create({
                'survey_id': self.id,
                'partner_id': supplier.id,
                'order_line': po_lines,
                'date_planned': planned_datetime,
            })
            created_pos += po
            
        self.purchase_order_create  = True

        # Retornar vista dinámica dependiendo si se creó 1 o varias POs
        if len(created_pos) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Orden de Compra'),
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'res_id': created_pos.id,
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Órdenes de Compra'),
                'res_model': 'purchase.order',
                'view_mode': 'list,form',
                'domain': [('id', 'in', created_pos.ids)],
            }


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("impsa.cylinder.survey")
                    or "Nuevo"
                )

        return super(CylinderSurvey, self).create(vals_list)
