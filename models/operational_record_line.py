from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class OperationalRecordLine(models.Model):
    _name = 'impsa.operational.record.line'
    _description = 'Línea de Registro Operativo'
    _order = 'sequence, id desc'

    group_id = fields.Many2one(
        'impsa.cylinder.group',
        string='Grupo',
        required=True,
        ondelete='cascade',
        index=True
    )

    survey_id = fields.Many2one(
        'impsa.cylinder.survey',
        string='Levantamiento',
        related='group_id.survey_id',
        store=True,
        index=True
    )

    sequence = fields.Integer(string='Secuencia', default=0)
    
    action_id = fields.Many2one(
        'impsa.apu.survey.actions',
        string='Trabajo a realizar',
        required=True,
        ondelete='restrict',
        help="Seleccione la acción estandarizada a realizar."
    )
    
    obs = fields.Text(string='Dimensiones / Observaciones')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('group_id'):
                group = self.env['impsa.cylinder.group'].browse(vals['group_id'])
                if group.survey_id.state != 'draft' and not self.env.context.get('skip_apu_sync'):
                    raise ValidationError(_(
                        "No se pueden agregar operaciones después de que el "
                        "levantamiento ha salido de la etapa inicial."
                    ))

        records = super().create(vals_list)

        if not self.env.context.get('skip_apu_sync'):
            apu_vals = [
                {
                    'apu_id': record.group_id.sudo().apu_id.id,
                    'action_id': record.action_id.id,
                    'obs': record.obs,
                    'operational_line_id': record.id,
                }
                for record in records
                if record.group_id.sudo().apu_id
            ]
            if apu_vals:
                self.env['impsa.apu.survey.line'].sudo() \
                    .with_context(skip_survey_sync=True) \
                    .create(apu_vals)

        return records


    def write(self, vals):
        records = self.exists()
        if not records:
            return True

        for record in records:
            if record.survey_id and record.survey_id.state != 'draft' and not self.env.context.get('skip_apu_sync'):
                raise ValidationError(_(
                    "No se pueden modificar operaciones en este estado (%s)."
                ) % record.survey_id.state)

        res = super(OperationalRecordLine, records).write(vals)

        if ('action_id' in vals or 'obs' in vals) and not self.env.context.get('skip_apu_sync'):
            records_with_apu = records.filtered(lambda r: r.group_id.sudo().apu_id)
            if records_with_apu:
                apu_lines = self.env['impsa.apu.survey.line'].sudo().search([
                    ('operational_line_id', 'in', records_with_apu.ids)
                ])
                if apu_lines:
                    vals_to_sync = {}
                    if 'action_id' in vals:
                        vals_to_sync['action_id'] = vals['action_id']
                    if 'obs' in vals:
                        vals_to_sync['obs'] = vals['obs']
                        
                    if vals_to_sync:
                        apu_lines.with_context(skip_survey_sync=True) \
                            .write(vals_to_sync)

        return res


    def unlink(self):
        records = self.exists()
        if not records:
            return True

        for record in records:
            if not record.group_id.exists():
                continue
            if record.survey_id and record.survey_id.state != 'draft' and not self.env.context.get('skip_apu_sync'):
                raise ValidationError(_(
                    "No se pueden eliminar operaciones en este estado."
                ))

        if not self.env.context.get('skip_apu_sync'):
            apu_lines = self.env['impsa.apu.survey.line'].sudo().search([
                ('operational_line_id', 'in', records.ids)
            ])
            if apu_lines:
                apu_lines.with_context(skip_survey_sync=True).unlink()

        return super(OperationalRecordLine, records).unlink()