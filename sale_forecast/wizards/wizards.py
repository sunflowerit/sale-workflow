from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleForecastSheet(models.TransientModel):
    _name = "sale.forecast.sheet"
    _inherits = {"stock.demand.estimate.sheet": "sheet_id"}
    _description = "Stock Demand Estimate Sheet"

    sheet_id = fields.Many2one(
        comodel_name="stock.demand.estimate.sheet", required=True, ondelete="cascade"
    )

    def button_validate(self):
        res = []
        for line in self.line_ids:
            if line.estimate_id:
                line.estimate_id.product_uom_qty = line.product_uom_qty
                res.append(line.estimate_id.id)
            else:
                data = self._prepare_estimate_data(line)
                estimate = self.env["sale.forecast"].create(data)
                res.append(estimate.id)
        res = {
            "domain": [("id", "in", res)],
            "name": _("Sale Forecast"),
            "src_model": "sale.forecast.wizard",
            "view_type": "form",
            "view_mode": "tree",
            "res_model": "sale.forecast",
            "type": "ir.actions.act_window",
        }
        return res

    @api.onchange(
        "date_start",
        "date_end",
        "date_range_type_id",
    )
    def _onchange_dates(self):
        return self.sheet_id._onchange_dates()

    @api.model
    def _prepare_estimate_data(self, line):
        return self.sheet_id._prepare_estimate_data(line)


class SaleForecastSheetLine(models.TransientModel):
    _name = "sale.forecast.sheet.line"
    _inherits = {"stock.demand.estimate.sheet.line": "sheet_line_id"}
    _description = "Stock Demand Estimate Sheet Line"

    sheet_line_id = fields.Many2one(
        comodel_name="stock.demand.estimate.sheet.line",
        required=True,
        ondelete="cascade",
    )


class SaleForecastWizard(models.TransientModel):
    _name = "sale.forecast.wizard"
    _inherits = {"stock.demand.estimate.wizard": "stock_wizard_id"}
    _description = "Sale Forecast Wizard"

    stock_wizard_id = fields.Many2one(
        comodel_name="stock.demand.estimate.wizard", required=True, ondelete="cascade"
    )

    def create_sheet(self):
        self.ensure_one()
        if not self.product_ids:
            raise UserError(_("You must select at least one product."))

        # 2d matrix widget need real records to work
        sheet = self.env["sale.forecast.sheet"].create(
            {
                "date_start": self.date_start,
                "date_end": self.date_end,
                "date_range_type_id": self.date_range_type_id.id,
                "location_id": self.location_id.id,
                "product_ids": [(6, 0, self.product_ids.ids)],
            }
        )
        sheet._onchange_dates()

        res = {
            "name": _("Forecast Sheet"),
            "src_model": "sale.forecast.wizard",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "res_model": "sale.forecast.sheet",
            "res_id": sheet.id,
            "type": "ir.actions.act_window",
        }
        return res
