from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CylinderImage(models.Model):
    _name = 'impsa.cylinder.image'
    _description = 'Imágenes del Cilindro'
    _order = 'group_id, cylinder_number, sequence, id desc'

    # relación principal al Grupo
    group_id = fields.Many2one(
        'impsa.cylinder.group', 
        string='Grupo de Cilindros', 
        required=True, 
        ondelete='cascade',
        index=True
    )

    group_name = fields.Char(related='group_id.name', string="Nombre del Grupo", readonly=True)
    group_qty = fields.Integer(related='group_id.quantity', string="Total en Grupo", readonly=True)
    
    survey_id = fields.Many2one(
        'impsa.cylinder.survey', 
        string='Levantamiento', 
        related='group_id.survey_id',
        store=True,
        index=True,
    )
    
    cylinder_number = fields.Integer(
        string="Número de Cilindro", 
        required=True, 
        default=1,
        help="Identifica a qué cilindro físico dentro del grupo corresponde esta imagen."
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

    @api.constrains('cylinder_number', 'group_id')
    def _check_cylinder_number(self):
        """Valida que el usuario no asigne una foto al 'Cilindro 4' si el grupo solo tiene 3."""
        for img in self:
            if img.cylinder_number < 1 or img.cylinder_number > img.group_id.quantity:
                raise ValidationError(_(
                    "El número de cilindro (%(cyl_num)s) debe estar entre 1 y la cantidad total del grupo (%(qty)s).",
                    cyl_num=img.cylinder_number,
                    qty=img.group_id.quantity
                ))

    @api.model_create_multi
    def create(self, vals_list):
        count_tracker = {}
        for vals in vals_list:
            if not vals.get('name'):
                comp = vals.get('component', 'misc')
                group = vals.get('group_id', False)
                cyl_num = vals.get('cylinder_number', 1)
                
                # llave de rastreo: (Grupo, Numero de cilindro, Componente)
                tracker_key = (group, cyl_num, comp)
                
                if tracker_key not in count_tracker:
                    existing_count = self.search_count([
                        ('group_id', '=', group),
                        ('cylinder_number', '=', cyl_num),
                        ('component', '=', comp)
                    ])
                    count_tracker[tracker_key] = existing_count
                
                count_tracker[tracker_key] += 1
                current_number = count_tracker[tracker_key]
                
                comp_upper = comp.upper()
                # formato de nomenclatura: IMG-CIL1-BARREL-1
                vals['name'] = f"IMG-CIL{cyl_num}-{comp_upper}-{current_number}"

        return super(CylinderImage, self).create(vals_list)