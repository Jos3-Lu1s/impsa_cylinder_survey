/** @odoo-module **/
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, onWillUpdateProps  } from "@odoo/owl";

export class DynamicQuantitySelect extends Component {
    static template = "impsa_cylinder_survey.DynamicQuantitySelect";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        // Monitoreamos cambios en los props para validar el valor actual
        onWillUpdateProps((nextProps) => {
            const newMax = nextProps.record.data.group_quantity || 0;
            const currentValue = nextProps.record.data[this.props.name];
            
            // Si el valor actual es mayor al nuevo máximo, reseteamos a 1 o 0
            if (currentValue > newMax && newMax > 0) {
                this.props.record.update({ [this.props.name]: 1 });
            } else if (newMax === 0) {
                this.props.record.update({ [this.props.name]: 0 });
            }
        });
    }

    /**
     * Genera dinámicamente las opciones basándose en el group_quantity
     */
    get options() {
        // Obtenemos la cantidad desde el record actual en la vista
        const qty = this.props.record.data.group_quantity || 0;
        let opts = [];
        for (let i = 1; i <= qty; i++) {
            opts.push({ value: i, label: `Cilindro ${i}` });
        }
        return opts;
    }

    /**
     * Actualiza el valor del campo en el ORM del cliente cuando el usuario selecciona
     */
    onChange(ev) {
        const val = parseInt(ev.target.value, 10);
        this.props.record.update({ [this.props.name]: val });
    }
}

registry.category("fields").add("dynamic_quantity_select", {
    component: DynamicQuantitySelect,
});