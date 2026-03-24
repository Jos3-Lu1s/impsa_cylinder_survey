/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class ImpsaImageGallery extends Component {
    static template = "impsa_cylinder_survey.ImageGallery";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.dialogService = useService("dialog");
        this.notification = useService("notification");
    }

    get records() {
        return this.props.record.data[this.props.name].records;
    }

    getImageUrl(rec) {
        if (rec.resId) {
            return `/web/image?model=impsa.cylinder.image&id=${rec.resId}&field=image&width=256&height=256`;
        }
        if (rec.data.image) {
            return `data:image/jpeg;base64,${rec.data.image}`;
        }
        return '/web/static/img/placeholder.png';
    }

    openRecord(rec) {
        if (rec.resId) {
            this.dialogService.add(FormViewDialog, {
                resModel: "impsa.cylinder.image",
                resId: rec.resId,
                title: "Detalle de Imagen",
                onRecordSaved: () => {
                    this.props.record.load();
                }
            });
        } else {
            this.notification.add(
                "Guarda el registro principal primero para ver detalles completos.", 
                { type: "warning" }
            );
        }
    }

    async onAddImage() {
        if (!this.props.record.resId) {
            this.notification.add(
                "Por favor, guarda el documento principal antes de agregar imágenes.", 
                { type: "danger" }
            );
            return;
        }

        this.dialogService.add(FormViewDialog, {
            resModel: "impsa.cylinder.image",
            context: {
                ...this.props.record.context, 
                default_group_id: this.props.record.resId,
            },
            title: "Añadir Imagen",
            onRecordSaved: () => {
                this.props.record.load(); 
            }
        });
    }

    async onDeleteImage(rec) {
        this.dialogService.add(ConfirmationDialog, {
            body: "¿Estás seguro de que deseas eliminar esta imagen de la galería?",
            confirm: async () => {
                await rec.delete();
            },
            cancel: () => {},
        });
    }

}

export const impsaImageGalleryField = {
    component: ImpsaImageGallery,
    supportedTypes: ["one2many", "many2many"],
};

registry.category("fields").add("impsa_image_gallery", impsaImageGalleryField);