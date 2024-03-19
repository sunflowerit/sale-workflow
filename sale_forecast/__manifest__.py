# Copyright 2016-20 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    "name": "Sale Forecast",
    "summary": "Enable forecast for Sales",
    "version": "16.0.1.0.0",
    "author": "Therp BV, Odoo Community Association (OCA)",
    "development_status": "Alpha",
    "website": "https://github.com/OCA/sale-workflow",
    "category": "Generic Modules/Sale",
    "depends": [
        "sale",
        "stock",
        "web_widget_x2many_2d_matrix",
        "date_range",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/sale_security.xml",
        "views/sale_forecast_view.xml",
        "wizards/sale_forecast_wizard_view.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
}
