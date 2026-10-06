from odoo import models
from odoo.tools.misc import format_date

# Fields that always carry an Odoo default; print them empty for hand-filling
BLANK_FIELDS = {"marital", "distance_home_work_unit"}


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def action_print_private_information(self):
        self.ensure_one()
        return self.env.ref(
            "employee_private_info_report.action_report_employee_private_info"
        ).report_action(self)

    def _pv(self, *names):
        """Printable value of the first existing field in names; '' if none or blank."""
        self.ensure_one()
        for name in names:
            field = self._fields.get(name)
            if not field:
                continue
            if name in BLANK_FIELDS:
                return ""
            value = self[name]
            if field.type == "many2one":
                return value.display_name or ""
            if field.type == "selection":
                sel = dict(field._description_selection(self.env))
                return sel.get(value, "") if value else ""
            if field.type in ("date", "datetime"):
                return format_date(self.env, value) if value else ""
            if field.type in ("integer", "float"):
                return str(value) if value else ""
            return value or ""
        return ""
