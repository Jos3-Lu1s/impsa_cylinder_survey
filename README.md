# Levantamiento de Cilindros IMPSA

## Descripción
**Levantamiento de Cilindros IMPSA** (Formato digital F-05-01) es un módulo de Odoo diseñado para la digitalización del formato F-05-01 utilizado en el levantamiento de cilindros hidráulicos.

Este módulo permite capturar medidas detalladas de los componentes principales de los cilindros y registrar los trabajos a realizar.

## Características Principales
* **Captura de Medidas:** Permite el registro de medidas de componentes clave como Camisa, Vástago, Pistón y Cabeza.
* **Registro de Trabajos:** Facilita la documentación de trabajos a realizar sobre los cilindros, tales como cromado, cambio de sellos, entre otros.
* **Integración:** Totalmente integrado con otros módulos base de Odoo como CRM, Ventas, Compras, Producción (MRP) y Recursos Humanos.

## Dependencias
Para que este módulo funcione correctamente, requiere los siguientes módulos de Odoo:
* `base`
* `crm`
* `mail`
* `purchase`
* `sale_crm`
* `sale_management`
* `mrp`
* `hr`

## Estructura del Proyecto
* `controllers/`: Controladores para endpoints web.
* `data/`: Datos iniciales, secuencias y configuración XML.
* `demo/`: Datos de demostración.
* `models/`: Definición de los modelos de base de datos (`cylinder_survey`, `apu_survey`, etc.).
* `reports/`: Plantillas y acciones para la generación de reportes en PDF/HTML.
* `security/`: Reglas de seguridad y listas de control de acceso (`ir.model.access.csv`).
* `static/`: Archivos estáticos como imágenes y estilos.
* `views/`: Definición de las vistas (formularios, árboles, kanban) para la interfaz de usuario de Odoo.

## Instalación
1. Clonar el repositorio en la carpeta de módulos personalizados (`addons`) de su instancia de Odoo.
2. Actualizar la lista de aplicaciones (Modo desarrollador activado).
3. Buscar **Levantamiento de Cilindros IMPSA** en las aplicaciones y hacer clic en **Instalar**.

## Autor
* **Desarrollador:** My Company
* **Sitio Web:** [https://www.yourcompany.com](https://www.yourcompany.com)

## Licencia
Este módulo se distribuye bajo la licencia **LGPL-3**.
