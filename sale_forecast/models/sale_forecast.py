from odoo import fields, models


class SaleForecast(models.Model):
    _name = "sale.forecast"
    _inherits = {"stock.demand.estimate": "stock_demand_id"}
    _description = "Sale forecast"

    stock_demand_id = fields.Many2one(
        comodel_name="stock.demand.estimate", required=True, ondelete="cascade"
    )
