# Copyright 2024 Therp BV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Sale Forecast",
    "summary": "Sale forecast report",
    "version": "16.0.1.0.0",
    "category": "Generic Modules/Sale",
    "author": "Therp BV, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-workflow",
    "depends": ["sale", "stock_demand_estimate", "stock_demand_estimate_matrix"],
    "data": [
        "security/ir.model.access.csv",
        "views/date_range.xml",
        "views/sale_forecast.xml",
        "wizards/wizard_view.xml",
    ],
    "license": "AGPL-3",
}
