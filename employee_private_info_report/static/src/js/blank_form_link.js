/** @odoo-module **/
import { registry } from "@web/core/registry";

// Route the "blank form" link through the web client's report handling, so
// report-preview modules can intercept it. If this script fails to load, the
// link's href still opens the PDF directly.
const blankFormLinkService = {
    dependencies: ["action"],
    start(env, { action }) {
        document.addEventListener("click", (ev) => {
            const link = ev.target.closest && ev.target.closest("a.o_pi_blank_link");
            if (!link) {
                return;
            }
            ev.preventDefault();
            action.doAction(
                "employee_private_info_report.action_report_employee_private_info"
            );
        });
    },
};

registry.category("services").add("pi_blank_link", blankFormLinkService);
