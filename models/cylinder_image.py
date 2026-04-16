from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CylinderImage(models.Model):
    _name = 'impsa.cylinder.image'
    _description = 'Imágenes del Cilindro'
    _order = 'group_id, sequence, id desc'

    cylinder_id = fields.Many2one(
        'impsa.cylinder',
        string="Cilindro Físico",
        required=True,
        ondelete="cascade",
        index=True
    )

    group_id = fields.Many2one(
        'impsa.cylinder.group', 
        string='Grupo de Cilindros', 
        related="cylinder_id.group_id",
        store=True,
        index=True
    )
    
    survey_id = fields.Many2one(
        'impsa.cylinder.survey', 
        string='Levantamiento', 
        related='cylinder_id.survey_id',
        store=True,
        index=True,
    )

    badge_ident_name=fields.Char(
        string="Nombre identificador imagen",
        related="cylinder_id.name",
        store=True
    )
    
    sequence = fields.Integer(string="Secuencia", default=10)
    name = fields.Char(string="Descripción")
    
    component = fields.Selection([
        ('barrel', 'Camisa'),
        ('rod', 'Vástago'),
        ('piston', 'Émbolo / Pistón'),
        ('head', 'Cabeza'),
        ('stroke', 'Carrera'),
        ('accessory', 'Accesorio'),
    ], string="Componente", required=True)

    image = fields.Image(string="Imagen", max_width=1920, max_height=1920, required=True)

    @api.model_create_multi
    def create(self, vals_list):
        count_tracker = {}
        for vals in vals_list:
            if not vals.get('name'):
                comp = vals.get('component', 'misc')
                cyl_id = vals.get('cylinder_id', False)
                
                # llave de rastreo: (Cilindro, Componente)
                tracker_key = (cyl_id, comp)
                
                if tracker_key not in count_tracker:
                    existing_count = self.search_count([
                        ('cylinder_id', '=', cyl_id),
                        ('component', '=', comp)
                    ])
                    count_tracker[tracker_key] = existing_count
                
                count_tracker[tracker_key] += 1
                current_number = count_tracker[tracker_key]
                
                comp_upper = comp.upper()
                
                # Buscamos el nombre del cilindro de forma segura
                cyl_obj = self.env['impsa.cylinder'].browse(cyl_id) if cyl_id else False
                cyl_name = cyl_obj.name.replace(' ', '').upper() if cyl_obj else "CIL"
                
                vals['name'] = f"IMG-{cyl_name}-{comp_upper}-{current_number}"

        return super(CylinderImage, self).create(vals_list)