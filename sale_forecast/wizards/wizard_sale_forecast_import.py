# pylint: disable=no-member,protected-access,invalid-name,no-self-use
import base64
import logging
from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class WizardSaleForecastImport(models.TransientModel):
    """Import sale forecast"""

    _name = "wizard.sale.forecast.import"
    _description = "Import sale forecast records"

    file_import = fields.Binary("Import Forecast")
    file_name = fields.Char("file name")

    def action_process_import(self):
        """Actually process the uploaded file to import it."""
        self.ensure_one()
        if not self.file_import:
            raise UserError(_("Please attach a file containing product information."))
        (
            rows,
            date_headers,
            default_code_index,
            date_index,
            key_index,
        ) = self._import_file()
        aggregate_info = self._aggregate_info(
            rows, date_headers, default_code_index, date_index, key_index
        )
        self._process_import(aggregate_info)

    def _import_file(self):
        def get_field_index(header_row, name):
            """Get index of column in input file."""
            try:
                index = header_row.index(name)
                return index
            except ValueError as error:
                raise UserError(
                    _("Row header name %s is not found in file") % name
                ) from error

        self.ensure_one()
        lst = self._get_rows()
        if not lst or not lst[0]:
            raise UserError(_("Import file is empty or unreadable"))
        rows = lst[1]
        header_row = rows[0]
        date_headers = header_row[4:]
        product_headers = header_row[:4]
        (product_category_index, product_index, default_code_index, key_index,) = (
            get_field_index(product_headers, name)
            for name in [
                "Product Category",
                "Product",
                "Item Code (SKU)",
                "Key",
            ]
        )
        date_index = []
        date_index += [get_field_index(header_row, name) for name in date_headers]
        return rows, date_headers, default_code_index, date_index, key_index

    def _get_rows(self):
        """Get rows from data_file."""
        self.ensure_one()
        import_model = self.env["base_import.import"]
        data_file = base64.b64decode(self.file_import)
        importer = import_model.create({"file": data_file, "file_name": self.file_name})
        return importer._read_file({"quoting": '"', "separator": ","})

    def _aggregate_info(
        self, rows, date_headers, default_code_index, date_index, key_index
    ):
        aggregate_info = dict()
        for row in rows[2:]:
            location = row[key_index].strip()
            if not location:
                continue
            if location == "Total":
                continue
            default_code = row[default_code_index].strip()
            aggregate_info[default_code] = aggregate_info.get(default_code, [])
            for date, index in zip(date_headers, date_index):
                quantity = (
                    float(row[index].replace(",", "").replace(".", ""))
                    if row[index]
                    else 0
                )
                if quantity <= 0:
                    continue
                if not quantity:
                    continue
                date_forecast = self._date_to_object(date.strip())
                if not date_forecast:
                    continue
                aggregate_info[default_code].append(
                    (
                        location,
                        date_forecast,
                        quantity,
                    )
                )
        return aggregate_info

    def _date_to_object(self, date):
        """No expired dates"""
        try:
            date_object = datetime.strptime(date, "%b-%y")
        except:
            try:
                date_object = datetime.strptime(date, "%y-%b")
            except:
                raise
        if date_object.date() < fields.Date.today():
            return False
        return date_object

    def _process_import(self, rows):
        forecast_model = self.env["sale.forecast"]
        location_model = self.env["stock.location"]
        location_dict = {
            "Sales": location_model.browse(25),
            "CS consumption": location_model.browse(30),
            "AS consumption": location_model.browse(18),
        }
        for default_code, location_date_quantity in rows.items():
            product = self.env["product.product"].search(
                [("default_code", "=", default_code)]
            )
            if not product:
                _logger.warning(
                    "No product with default code %s exists.",
                    default_code,
                )
                continue
            if not location_date_quantity:
                continue
            for location, date, quantity in location_date_quantity:
                if location not in location_dict.keys():
                    _logger.warning(
                        "No location %s exists.",
                        location,
                    )
                    continue
                location_id = location_dict.get(location)
                if not location_id:
                    _logger.warning(
                        "No location %s exists.",
                        location,
                    )
                    continue
                date_range_id = self._get_date_range_id(date)
                if not date_range_id:
                    _logger.warning(
                        "No monthly date range exists for %s.",
                        date.strftime("%b-%y"),
                    )
                    continue
                vals = {
                    "product_id": product.id,
                    "location_id": location_id.id,
                    "product_uom_qty": quantity,
                    "date_range_id": date_range_id.id,
                }
                existing_forecast = forecast_model.search(
                    [
                        ("product_id", "=", vals["product_id"]),
                        ("date_range_id", "=", vals["date_range_id"]),
                        ("location_id", "=", vals["location_id"]),
                    ]
                )
                if existing_forecast:
                    _logger.warning(
                        "Forecast for product %s, location %s, date %s exists, updating...",
                        (product.name, location, date.strftime("%b-%y")),
                    )
                    existing_forecast.write(vals)
                    continue
                forecast_model.create(vals)

    def _get_date_range_id(self, date):
        date_range_domain = [
            ("date_start", "<=", date),
            ("date_end", ">", date),
            ("type_name", "ilike", "Monthly"),
            ("active", "=", True),
        ]
        return self.env["date.range"].search(date_range_domain)
